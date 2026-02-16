import numpy as np
import random

class HeartModel:
    def __init__(self, age: int, resting_hr: int, max_hr: int = None):
        self.age = age
        self.resting_hr = resting_hr
        self.max_hr = max_hr if max_hr else (220 - age)
        
        # State
        self.current_hr = float(resting_hr) # Ensure float from the start
        self.cumulative_trimp = 0.0
        
        # Recovery logic
        self.is_recovering = False
        self.recovery_start_hr = 0
        self.seconds_since_recovery_start = 0.0 # Internal counter
        self.hrr_score = 0
        self.hrr_calculated = False 

    def simulate_step(self, intensity: float, dt: float = 1.0, temperature: float = 20.0):
        """
        Advance the simulation by one step.
        dt: delta time in seconds (default 1 second per tick)
        temperature: environmental temperature in Celsius
        """
        previous_hr = self.current_hr
        
        # 1. Calculation of Base Target based on Intensity (Running/Walking)
        target_hr_intensity = self.resting_hr + (self.max_hr - self.resting_hr) * intensity
        
        # 2. (NIVEL 4 FEATURE) Temperature Adjustment
        # Logic: Heat creates drift upward due to thermoregulation
        temp_drift = 0.0
        if temperature > 25.0:
            # Heat: +1 bpm for every degree above 25°C
            temp_drift = (temperature - 25.0) * 1.0
        elif temperature < 5.0:
            # Cold: +0.5 bpm for every degree below 5°C (vasoconstriction stress)
            temp_drift = (5.0 - temperature) * 0.5
            
        # The new Target is Activity + Weather Stress
        final_target_hr = target_hr_intensity + temp_drift

        # 3. Physiological inertia (Alpha blending)
        # If dt is 1 second, this works. If dt changes, alpha should be adjusted.
        alpha = 0.1 if final_target_hr >= self.current_hr else 0.05
        self.current_hr = (self.current_hr * (1 - alpha)) + (final_target_hr * alpha)

        # 4. Detection of recovery start
        # (If intensity drops to 0 and we were high)
        if intensity == 0 and previous_hr > (self.resting_hr + 20) and not self.is_recovering:
            self.is_recovering = True
            self.recovery_start_hr = previous_hr
            self.seconds_since_recovery_start = 0.0
        
        # 5. Recovery time counting
        if self.is_recovering:
            self.seconds_since_recovery_start += dt

            # Check if we passed the minute mark (approx 60 secs)
            if 60.0 <= self.seconds_since_recovery_start <= 61.0 and not self.hrr_calculated:
                self.hrr_score = float(round(self.recovery_start_hr - previous_hr, 1))
                self.hrr_calculated = True
                print(f"✅ [BIOMETRICS] HRR Calculated: {self.hrr_score} BPM recovery")
            
            # If we start exercising again, cancel the recovery
            if intensity > 0:
                self.is_recovering = False
                self.seconds_since_recovery_start = 0.0
                self.hrr_calculated = False

        # 6. TRIMP calculation (Banister's algorithm)
        hr_reserve = (self.current_hr - self.resting_hr) / (self.max_hr - self.resting_hr + 1)
        if hr_reserve < 0: hr_reserve = 0
        
        # Integrate TRIMP based on elapsed time (dt / 60 because TRIMP is per minute)
        trimp_increase = dt * (1/60) * hr_reserve * np.exp(1.92 * hr_reserve)
        self.cumulative_trimp += float(trimp_increase)

        # 7. Natural Variation (Jitter)
        variation = random.uniform(-0.5, 0.5) 
        self.current_hr += variation

        # Safety clamp (para que el drift de temperatura no cause valores irreales)
        if self.current_hr > 230: self.current_hr = 230
        if self.current_hr < 30: self.current_hr = 30

        return self.get_metrics()

    def get_metrics(self):
        return {
            "bpm": float(round(self.current_hr, 1)),
            "trimp": float(round(self.cumulative_trimp, 2)),
            "hrr": float(round(self.hrr_score, 1)),
            "zone": self._get_zone(),
            "color": self._get_zone_color()
        }

    def _get_zone(self):
        percent = self.current_hr / self.max_hr
        if percent < 0.6: return "Rest"
        if percent < 0.7: return "Fat Burn"
        if percent < 0.8: return "Aerobic"
        if percent < 0.9: return "Anaerobic"
        return "VO2 Max"

    def _get_zone_color(self):
        colors = {
            "Rest": "#00FF00",      
            "Fat Burn": "#FFFF00", 
            "Aerobic": "#FFA500",  
            "Anaerobic": "#FF4500", 
            "VO2 Max": "#FF0000"    
        }
        return colors.get(self._get_zone(), "#FFFFFF")