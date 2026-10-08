-- DDL for Dimensional and Fact Tables for Solar Energy & Weather Analytics
-- Primary keys enforced on date / hour_ts to ensure idempotent upserts

CREATE TABLE IF NOT EXISTS `dim_date` (
    `date` VARCHAR(30) PRIMARY KEY,
    `date_key` INT,
    `year` INT,
    `quarter` INT,
    `quarter_name` VARCHAR(20),
    `month_number` INT,
    `month_name` VARCHAR(20),
    `year_month` VARCHAR(10),
    `week_of_year` INT,
    `day_of_month` INT,
    `day_of_week_number` INT,
    `day_name` VARCHAR(20),
    `day_of_year` INT,
    `season` VARCHAR(20),
    `is_weekend` BOOLEAN,
    INDEX `idx_dim_date_season` (`season`),
    INDEX `idx_dim_date_year_month` (`year_month`)
);

CREATE TABLE IF NOT EXISTS `fact_solar_daily` (
    `date` VARCHAR(30) PRIMARY KEY,
    `generation_kwh` FLOAT,
    `consumption_kwh` FLOAT,
    `grid_feed_in_kwh` FLOAT,
    `grid_purchase_kwh` FLOAT,
    `charge_kwh` FLOAT,
    `discharge_kwh` FLOAT,
    INDEX `idx_solar_daily_gen` (`generation_kwh`)
);

CREATE TABLE IF NOT EXISTS `fact_weather_daily` (
    `date` VARCHAR(30) PRIMARY KEY,
    `shortwave_radiation_sum` FLOAT,
    `sunshine_duration` FLOAT,
    `daylight_duration` FLOAT,
    `cloud_cover_mean` FLOAT,
    `temperature_2m_mean` FLOAT,
    `relative_humidity_2m_mean` FLOAT,
    `rain_sum` FLOAT,
    `wind_speed_10m_mean` FLOAT,
    `weather_code` INT,
    INDEX `idx_weather_daily_temp` (`temperature_2m_mean`),
    INDEX `idx_weather_daily_rad` (`shortwave_radiation_sum`)
);

CREATE TABLE IF NOT EXISTS `fact_solar_hourly` (
    `hour_ts` VARCHAR(50) PRIMARY KEY,
    `date` VARCHAR(30),
    `generation_kwh` FLOAT,
    `consumption_kwh` FLOAT,
    `grid_feed_in_kwh` FLOAT,
    `grid_purchase_kwh` FLOAT,
    `charge_kwh` FLOAT,
    `discharge_kwh` FLOAT,
    `battery_soc_eoh` FLOAT,
    INDEX `idx_solar_hourly_date` (`date`)
);

CREATE TABLE IF NOT EXISTS `fact_weather_hourly` (
    `hour_ts` VARCHAR(50) PRIMARY KEY,
    `date` VARCHAR(30),
    `relative_humidity_2m` FLOAT,
    `wind_speed_10m` FLOAT,
    `is_day` INT,
    `sunshine_duration` FLOAT,
    `temperature_2m` FLOAT,
    `cloud_cover` FLOAT,
    `rain` FLOAT,
    `weather_code` INT,
    INDEX `idx_weather_hourly_date` (`date`)
);

CREATE TABLE IF NOT EXISTS `etl_runs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `run_id` VARCHAR(64) UNIQUE,
    `start_time` DATETIME,
    `end_time` DATETIME,
    `status` VARCHAR(20),
    `records_processed` INT,
    `details` JSON,
    `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_etl_status` (`status`),
    INDEX `idx_etl_timestamp` (`timestamp`)
);
