CREATE TABLE IF NOT EXISTS prediction_logs (
 id INT AUTO_INCREMENT PRIMARY KEY,
 shortwave_radiation FLOAT,
 sunshine_duration FLOAT,
 cloud_cover FLOAT,
 temperature_2m FLOAT,
 wind_speed_10m FLOAT,
 rain FLOAT,
 is_weekend INT,
 season VARCHAR(50),
 predicted_kwh FLOAT,
 timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);