"""
API Documentation - Solar Analytics
"""

API_DOCS = {
    "openapi": "3.0.0",
    "info": {
        "title": "Solar Energy Analytics API",
        "description": "Real-time solar energy generation prediction and analytics API",
        "version": "1.0.0",
        "contact": {
            "name": "Om Patel",
            "email": "patelom2810@gmail.com"
        }
    },
    "servers": [
        {
            "url": "http://127.0.0.1:8000",
            "description": "Development Server"
        }
    ],
    "paths": {
        "/": {
            "get": {
                "summary": "Predictor Form Homepage",
                "description": "Returns the main predictor form page",
                "tags": ["Pages"],
                "responses": {
                    "200": {
                        "description": "HTML form page",
                        "content": {"text/html": {}}
                    }
                }
            }
        },
        "/dashboard": {
            "get": {
                "summary": "Analytics Dashboard",
                "description": "Returns the analytics dashboard page",
                "tags": ["Pages"],
                "responses": {
                    "200": {
                        "description": "HTML dashboard page",
                        "content": {"text/html": {}}
                    }
                }
            }
        },
        "/api/dashboard-data": {
            "get": {
                "summary": "Get Dashboard Data",
                "description": "Retrieve all dashboard data including KPIs and chart data",
                "tags": ["Dashboard"],
                "responses": {
                    "200": {
                        "description": "Dashboard data",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "total_generation": {"type": "number"},
                                        "total_consumption": {"type": "number"},
                                        "self_sufficiency": {"type": "number"},
                                        "avg_temperature": {"type": "number"},
                                        "daily_data": {"type": "array"},
                                        "monthly_data": {"type": "array"},
                                        "radiation_data": {"type": "array"},
                                        "weather_distribution": {"type": "object"},
                                        "hourly_data": {"type": "array"}
                                    }
                                }
                            }
                        }
                    },
                    "500": {"description": "Server error"}
                }
            }
        },
        "/predict": {
            "post": {
                "summary": "Make Solar Generation Prediction",
                "description": "Predict solar generation based on weather parameters",
                "tags": ["Prediction"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["shortwave_radiation_sum", "sunshine_duration", "cloud_cover_mean",
                                           "temperature_2m_mean", "wind_speed_10m_mean", "rain_sum", "season", "is_weekend"],
                                "properties": {
                                    "shortwave_radiation_sum": {
                                        "type": "number",
                                        "description": "Shortwave radiation (0-500 W/m²)",
                                        "example": 25.0
                                    },
                                    "sunshine_duration": {
                                        "type": "number",
                                        "description": "Sunshine duration (0-86400 seconds)",
                                        "example": 39000
                                    },
                                    "cloud_cover_mean": {
                                        "type": "number",
                                        "description": "Cloud cover (0-100 %)",
                                        "example": 30.0
                                    },
                                    "temperature_2m_mean": {
                                        "type": "number",
                                        "description": "Temperature (-50 to 60 °C)",
                                        "example": 26.0
                                    },
                                    "wind_speed_10m_mean": {
                                        "type": "number",
                                        "description": "Wind speed (0-50 m/s)",
                                        "example": 17.5
                                    },
                                    "rain_sum": {
                                        "type": "number",
                                        "description": "Rain sum (0-500 mm)",
                                        "example": 0.0
                                    },
                                    "season": {
                                        "type": "string",
                                        "description": "Season",
                                        "enum": ["Dry", "Wet"],
                                        "example": "Dry"
                                    },
                                    "is_weekend": {
                                        "type": "boolean",
                                        "description": "Is weekend",
                                        "example": False
                                    }
                                }
                            },
                            "examples": {
                                "sunny_day": {
                                    "value": {
                                        "shortwave_radiation_sum": 30.0,
                                        "sunshine_duration": 40000,
                                        "cloud_cover_mean": 10.0,
                                        "temperature_2m_mean": 28.0,
                                        "wind_speed_10m_mean": 5.0,
                                        "rain_sum": 0.0,
                                        "season": "Dry",
                                        "is_weekend": True
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Prediction successful",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "predicted_generation_kwh": {"type": "number"},
                                        "status": {"type": "string", "enum": ["Low", "Normal"]}
                                    }
                                },
                                "example": {
                                    "predicted_generation_kwh": 38.5,
                                    "status": "Normal"
                                }
                            }
                        }
                    },
                    "400": {"description": "Validation failed"},
                    "503": {"description": "Model not available"}
                }
            }
        },
        "/history": {
            "get": {
                "summary": "Get Prediction History",
                "description": "Retrieve recent prediction history from database",
                "tags": ["Prediction"],
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "description": "Number of records to retrieve (max 1000)",
                        "schema": {"type": "integer", "default": 100}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Prediction history",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "predictions": {"type": "array"},
                                        "count": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/stats": {
            "get": {
                "summary": "Get Prediction Statistics",
                "description": "Get aggregated statistics about predictions",
                "tags": ["Statistics"],
                "responses": {
                    "200": {
                        "description": "Prediction statistics",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "total_predictions": {"type": "integer"},
                                        "avg_generation": {"type": "number"},
                                        "min_generation": {"type": "number"},
                                        "max_generation": {"type": "number"},
                                        "predictions_made_today": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/api/model-score": {
            "get": {
                "summary": "Get Model Performance Metrics",
                "description": "Get machine learning model evaluation metrics and feature importances",
                "tags": ["Model"],
                "responses": {
                    "200": {
                        "description": "Model metrics",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "model_type": {"type": "string"},
                                        "r2_score": {"type": "number"},
                                        "mae": {"type": "number"},
                                        "rmse": {"type": "number"},
                                        "mape": {"type": "number"},
                                        "n_samples": {"type": "integer"},
                                        "feature_importances": {"type": "object"},
                                        "predictions_vs_actual": {"type": "array"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/health": {
            "get": {
                "summary": "Health Check",
                "description": "Check application health status",
                "tags": ["System"],
                "responses": {
                    "200": {
                        "description": "Application is healthy",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "status": {"type": "string", "enum": ["healthy", "unhealthy"]},
                                        "model": {"type": "string"},
                                        "database": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
