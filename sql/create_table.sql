CREATE TABLE IF NOT EXISTS prediction_logs (
 id INT AUTO_INCREMENT PRIMARY KEY,
 prediction_time DATETIME DEFAULT CURRENT_TIMESTAMP,
 shortwave_radiation FLOAT,
 sunshine_duration FLOAT,
 cloud_cover FLOAT,
 temperature_2m FLOAT,
 wind_speed_10m FLOAT,
 rain FLOAT,
 is_weekend BOOLEAN,
 season VARCHAR(20),
 predicted_kwh FLOAT,
 actual_kwh FLOAT NULL
);