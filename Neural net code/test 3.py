import time, json, requests, joblib, threading
import cv2, numpy as np, tensorflow as tf
from ultralytics import YOLO

# ---------------- CONFIG ----------------
BLYNK_TOKEN = "sXz1_q-z-89Io6eWlEWsFT7OH4k6d1f8"
BLYNK_BASE  = "https://blynk.cloud/external/api"
VPINS = {
    "NOx":0,"CO":1,"MQ135":2,"Temp":3,"Hum":4,
    "US_F":5,"US_L":6,"US_R":7,"US_B":8,
    "FlameLED":9,"Rs_NOx":10,"Rs_CO":11,"Status":12,"GPS":10
}

SOURCE_CANDIDATES = [0]

MODEL_INJURED = r"C:\Users\Samiul Sazid\OneDrive\Desktop\project\bestt.pt"
MODEL_FIRE    = r"C:\Users\Samiul Sazid\OneDrive\Desktop\project\best.pt"
MODEL_COCO    = "yolov8n.pt"
MODEL_NN      = r"C:\Users\Samiul Sazid\OneDrive\Desktop\project\sensor_decision_model.h5"
SCALER_PATH   = r"C:\Users\Samiul Sazid\OneDrive\Desktop\project\scaler.pkl"
ENCODER_PATH  = r"C:\Users\Samiul Sazid\OneDrive\Desktop\project\label_encoder.pkl"

# Tuning
INFER_FRAME_W = 320
INFER_FRAME_H = 320
YOLO_SLEEP_S  = 0.03
SENSOR_POLL_S = 1.0
BLYNK_PUSH_S  = 1.5
SAFE_DISTANCE_CM = 15

DRAW = True
SHOW_WINDOW = True

# ---------------- SMOOTHING ----------------
US_BUFFER_SIZE = 3
GAS_BUFFER_SIZE = 3
us_history = {k: [0]*US_BUFFER_SIZE for k in ["US_F","US_L","US_R","US_B"]}
mq_history = {"MQ135":[0]*GAS_BUFFER_SIZE, "FlameLED":[0]*GAS_BUFFER_SIZE}
yolo_inj_history, yolo_fire_history = [], []

def moving_avg(history, key, new_val):
    history[key].append(new_val)
    if len(history[key]) > US_BUFFER_SIZE: history[key].pop(0)
    return sum(history[key])/len(history[key])

def safe_float(x, default=0.0):
    try: return float(x)
    except: return default

def blynk_get(vpin:int):
    try:
        r = requests.get(f"{BLYNK_BASE}/get?token={BLYNK_TOKEN}&V{vpin}", timeout=3)
        if r.status_code == 200:
            txt = r.text.strip()
            if txt.startswith('['):
                arr = json.loads(txt)
                if not arr: return 0.0
                return arr[0] if vpin==VPINS["GPS"] else safe_float(arr[0],0.0)
            return txt if vpin==VPINS["GPS"] else safe_float(txt,0.0)
    except: return 0.0

def blynk_set(vpin:int,value):
    try:
        requests.get(f"{BLYNK_BASE}/update?token={BLYNK_TOKEN}&V{vpin}={requests.utils.quote(str(value))}", timeout=2)
    except: pass

def try_open_video(sources):
    for s in sources:
        cap = cv2.VideoCapture(s)
        if cap.isOpened():
            print("[INFO] Opened video source:", s)
            return cap
    raise RuntimeError("No video source available")

# ---------------- LOAD MODELS ----------------
print("[INFO] Loading YOLO models...")
yolo_injured = YOLO(MODEL_INJURED)
yolo_fire    = YOLO(MODEL_FIRE)
yolo_coco    = YOLO(MODEL_COCO)

print("[INFO] Loading sensor NN + scaler + encoder...")
scaler  = joblib.load(SCALER_PATH)
encoder = joblib.load(ENCODER_PATH)
nn_model = tf.keras.models.load_model(MODEL_NN)

# ---------------- SHARED STATE ----------------
frame_lock = threading.Lock()
latest_frame, latest_small = None, None
stop_flag = False

yolo_lock = threading.Lock()
yolo_results = {"inj_seen": False,"fire_seen": False,"inj_boxes":[],"fire_boxes":[],"coco_boxes":[]}

sensor_lock = threading.Lock()
sensor_vec = np.zeros((1,8), dtype=np.float32)
last_blynk_push = 0.0

# ---------------- THREADS ----------------
def camera_thread():
    global latest_frame, latest_small, stop_flag
    cap = try_open_video(SOURCE_CANDIDATES)
    while not stop_flag:
        ok, frame = cap.read()
        if not ok: time.sleep(0.05); continue
        with frame_lock:
            latest_frame = frame.copy()
            latest_small = cv2.resize(frame,(INFER_FRAME_W,INFER_FRAME_H))
        time.sleep(0.005)
    cap.release()

def extract_boxes(res, sx, sy, conf_thresh=0.75):
    boxes=[]
    try:
        xyxy = res.boxes.xyxy.cpu().numpy()
        confs = res.boxes.conf.cpu().numpy()
        clses = res.boxes.cls.cpu().numpy().astype(int)
        for i in range(len(xyxy)):
            if confs[i] < conf_thresh: continue
            x1,y1,x2,y2 = xyxy[i]
            cls = clses[i]
            name = res.names.get(cls,str(cls)) if hasattr(res,"names") else str(cls)
            boxes.append((int(x1*sx),int(y1*sy),int(x2*sx),int(y2*sy),name,float(confs[i])))
    except Exception as e:
        print("[WARN] extract_boxes failed:", e)
    return boxes

def yolo_thread():
    global yolo_results, latest_small, latest_frame, stop_flag
    SMOOTH_FRAMES = 3
    while not stop_flag:
        with frame_lock:
            small = latest_small.copy() if latest_small is not None else None
            full = latest_frame.copy() if latest_frame is not None else None
        if small is None or full is None: time.sleep(0.05); continue

        fh, fw = full.shape[:2]
        sx, sy = fw/INFER_FRAME_W, fh/INFER_FRAME_H

        try:
            res_inj = yolo_injured.predict(small, conf=0.5, iou=0.5)[0]
            res_fire= yolo_fire.predict(small, conf=0.5, iou=0.5)[0]
            res_coco= yolo_coco.predict(small, conf=0.5, iou=0.5)[0]
        except Exception as e:
            print("[WARN] YOLO failed:",e); time.sleep(YOLO_SLEEP_S); continue

        inj_boxes = extract_boxes(res_inj, sx, sy, conf_thresh=0.5)
        fire_boxes = extract_boxes(res_fire, sx, sy, conf_thresh=0.5)
        coco_boxes = extract_boxes(res_coco, sx, sy, conf_thresh=0.5)

        yolo_inj_history.append(inj_boxes)
        if len(yolo_inj_history)>SMOOTH_FRAMES: yolo_inj_history.pop(0)
        yolo_fire_history.append(fire_boxes)
        if len(yolo_fire_history)>SMOOTH_FRAMES: yolo_fire_history.pop(0)

        smoothed_inj=[b for f in yolo_inj_history for b in f]
        smoothed_fire=[b for f in yolo_fire_history for b in f]

        with yolo_lock:
            yolo_results.update({
                "inj_seen": len(smoothed_inj)>0,
                "fire_seen": len(smoothed_fire)>0,
                "inj_boxes": smoothed_inj,
                "fire_boxes": smoothed_fire,
                "coco_boxes": coco_boxes
            })

        time.sleep(YOLO_SLEEP_S)

def blynk_reader_thread():
    global sensor_vec, stop_flag
    while not stop_flag:
        vals=[blynk_get(VPINS[s]) for s in ["US_F","US_L","US_R","US_B","MQ135","FlameLED","Temp","Hum"]]
        vals=[safe_float(v,0.0) for v in vals]
        with sensor_lock: sensor_vec[0,:]=np.array(vals,dtype=np.float32)
        time.sleep(SENSOR_POLL_S)

# ---------------- NN ----------------
def run_sensor_nn_local(vec8):
    Xs=scaler.transform(vec8)
    preds=nn_model.predict(Xs,verbose=0)
    idx=int(np.argmax(preds[0]))
    return encoder.classes_[idx] if hasattr(encoder,"classes_") else f"CLASS_{idx}",None,None

# ---------------- DECISION ----------------
def make_decision(us_f,us_l,us_r,us_b,gas_flag,flame_flag):
    if gas_flag>=0.5 or flame_flag>=0.5: return "STOP (HAZARD)"
    if us_f<SAFE_DISTANCE_CM:
        if us_l>us_r and us_l>SAFE_DISTANCE_CM: return "TURN LEFT"
        elif us_r>us_l and us_r>SAFE_DISTANCE_CM: return "TURN RIGHT"
        else: return "STOP"
    return "GO STRAIGHT"

def draw_sensor_window(vec,us_f,us_l,us_r,us_b,flame_flag,gas_flag,decision,gps_text=""):
    w,h=420,380
    win=np.zeros((h,w,3),dtype=np.uint8)+40
    y,lh=30,28
    cv2.putText(win,f"US_F: {us_f:.1f} cm",(10,y),0,0.7,(255,255,255),2); y+=lh
    cv2.putText(win,f"US_L: {us_l:.1f} cm",(10,y),0,0.7,(255,255,255),2); y+=lh
    cv2.putText(win,f"US_R: {us_r:.1f} cm",(10,y),0,0.7,(255,255,255),2); y+=lh
    cv2.putText(win,f"US_B: {us_b:.1f} cm",(10,y),0,0.7,(255,255,255),2); y+=lh
    cv2.putText(win,f"Flame: {flame_flag:.2f}",(10,y),0,0.7,(0,0,255),2); y+=lh
    cv2.putText(win,f"MQ135: {gas_flag:.2f}",(10,y),0,0.7,(0,255,0),2); y+=lh
    cv2.putText(win,f"Temp: {vec[0,6]:.1f}C",(10,y),0,0.7,(255,165,0),2); y+=lh
    cv2.putText(win,f"Hum: {vec[0,7]:.1f}%",(10,y),0,0.7,(255,165,0),2); y+=lh
    y+=10
    cv2.putText(win,"--- NAVIGATION ---",(10,y),0,0.7,(0,255,255),2); y+=lh
    col=(0,255,0) if "GO" in decision else (0,0,255) if "STOP" in decision else (0,165,255)
    cv2.putText(win,decision,(10,y),0,0.9,col,3); y+=lh
    if gps_text: cv2.putText(win,f"GPS: {gps_text}",(10,y),0,0.6,(200,200,0),2)
    return win

# ---------------- MAIN ----------------
def main():
    global stop_flag,last_blynk_push
    threading.Thread(target=camera_thread,daemon=True).start()
    threading.Thread(target=yolo_thread,daemon=True).start()
    threading.Thread(target=blynk_reader_thread,daemon=True).start()

    while not stop_flag:
        with frame_lock:
            if latest_frame is None: time.sleep(0.02); continue
            frame=latest_frame.copy()
        with sensor_lock: vec=sensor_vec.copy()

        flame_flag=moving_avg(mq_history,"FlameLED",float(vec[0,5]))
        gas_flag=moving_avg(mq_history,"MQ135",float(vec[0,4]))
        us_f=moving_avg(us_history,"US_F",float(vec[0,0]))
        us_l=moving_avg(us_history,"US_L",float(vec[0,1]))
        us_r=moving_avg(us_history,"US_R",float(vec[0,2]))
        us_b=moving_avg(us_history,"US_B",float(vec[0,3]))

        decision_label,_,_=run_sensor_nn_local(vec)
        decision=make_decision(us_f,us_l,us_r,us_b,gas_flag,flame_flag)

        gps_text=str(blynk_get(VPINS["GPS"]))

        # Push status to Blynk
        now=time.time()
        if now-last_blynk_push>BLYNK_PUSH_S:
            blynk_set(VPINS["Status"],decision)
            last_blynk_push=now

        if DRAW:
            with yolo_lock:
                for (x1,y1,x2,y2,l,c) in yolo_results["inj_boxes"]:
                    cv2.rectangle(frame,(x1,y1),(x2,y2),(0,0,255),2)
                    cv2.putText(frame,f"{l} {c:.2f}",(x1,y1-5),0,0.5,(0,0,255),2)
                for (x1,y1,x2,y2,l,c) in yolo_results["fire_boxes"]:
                    cv2.rectangle(frame,(x1,y1),(x2,y2),(0,165,255),2)
                    cv2.putText(frame,f"{l} {c:.2f}",(x1,y1-5),0,0.5,(0,165,255),2)
                for (x1,y1,x2,y2,l,c) in yolo_results["coco_boxes"]:
                    cv2.rectangle(frame,(x1,y1),(x2,y2),(255,255,0),2)
                    cv2.putText(frame,f"{l} {c:.2f}",(x1,y1-5),0,0.5,(255,255,0),2)

        if SHOW_WINDOW:
            sensor_win=draw_sensor_window(vec,us_f,us_l,us_r,us_b,flame_flag,gas_flag,decision,gps_text)
            cv2.imshow("Navigation Window",sensor_win)
            cv2.imshow("Surveillance Bot",frame)

        if cv2.waitKey(1)&0xFF==27:
            stop_flag=True; break

    cv2.destroyAllWindows()

if __name__=="__main__":
    main()
