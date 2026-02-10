import numpy as np


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

    def simulate_step(self, intensity: float, dt: float = 1.0):
        """
        Advance the simulation by one step.
        dt: delta time in seconds (default 1 second per tick)
        """
        previous_hr = self.current_hr
        target_hr = self.resting_hr + (self.max_hr - self.resting_hr) * intensity
        
        # Physiological inertia
        # If dt is 1 second, this works. If dt changes, alpha should be adjusted.
        alpha = 0.1 if target_hr >= self.current_hr else 0.05
        self.current_hr = (self.current_hr * (1 - alpha)) + (target_hr * alpha)

        # 1. Detection of recovery start
        # (If intensity drops to 0 and we were high)
        if intensity == 0 and previous_hr > (self.resting_hr + 20) and not self.is_recovering:
            self.is_recovering = True
            self.recovery_start_hr = previous_hr
            self.seconds_since_recovery_start = 0.0
        
        # 2. Recovery time counting
        if self.is_recovering:
            self.seconds_since_recovery_start += dt
            
            # Check if we passed the minute mark (approx 60 secs)
            # Use a small range to avoid missing it if dt is variable
            if 60.0 <= self.seconds_since_recovery_start <= 61.0 and self.hrr_score == 0:
                self.hrr_score = self.recovery_start_hr - self.current_hr
            
            # If we start exercising again, cancel the recovery
            if intensity > 0:
                self.is_recovering = False
                self.seconds_since_recovery_start = 0

        # TRIMP calculation (Banister's algorithm)
        hr_reserve = (self.current_hr - self.resting_hr) / (self.max_hr - self.resting_hr + 1)
        if hr_reserve < 0: hr_reserve = 0
        
        # Integrate TRIMP based on elapsed time (dt / 60 because TRIMP is per minute)
        trimp_increase = dt * (1/60) * hr_reserve * np.exp(1.92 * hr_reserve)
        self.cumulative_trimp += float(trimp_increase)

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