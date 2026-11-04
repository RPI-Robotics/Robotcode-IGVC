import odrive # Docs: https://docs.odriverobotics.com/v/latest/guides/python-package.html
import time
import pandas as pd
import os
odrive.get_device_manager().default_interfaces = {"can:can0"}

odrv0, odrv1 = odrive.find_sync(count=2)
t0 = time.monotonic()

data = {
    "odrv0_vel_des": [],
    "odrv1_vel_des": [],
    "odrv0_vel_meas": [],
    "odrv1_vel_meas": [],
    "odrv0_curr": [],
    "odrv1_curr": [],
    "timestamp": []
}

while True:
    t = time.monotonic() - t0
    data["odrv0_vel_des"].append(odrv0.axis0.controller.input_vel)
    data["odrv1_vel_des"].append(odrv1.axis0.controller.input_vel)

    data["odrv0_vel_meas"].append(odrv0.axis0.vel_estimate)
    data["odrv1_vel_meas"].append(odrv1.axis0.vel_estimate)

    data["odrv0_current"].append(odrv0.ibus)
    data["odrv1_current"].append(odrv1.ibus)
    
    data["timestamp"].append(t)

    df = pd.DataFrame(data)

    file_exists = os.path.isfile("output_pandas.csv")

    df.to_csv('output_pandas.csv', mode = 'a', header= not file_exists, index=False)

