import numpy as np
import random
from collections import deque


class HeartProfile:
    """Base class for the Digital Twin contexts."""
    def update_metrics(self, current_hr, resting_hr, max_hr, dt, intensity):
        pass
    
    def get_state(self):
        return {}

class AthleteProfile(HeartProfile):
    """Profile for the Kaggle athlete (TRIMP fatigue accumulation)"""
    def __init__(self, sex: str):
        self.sex = sex.lower()
        self.cumulative_trimp = 0.0

    def update_metrics(self, current_hr, resting_hr, max_hr, dt, intensity):
        # Calculation of TRIMP Exponential (Banister, 1991) 
        hr_reserve_fraction = (current_hr - resting_hr) / max(1.0, (max_hr - resting_hr))
        hr_reserve_fraction = max(0.0, hr_reserve_fraction)
        
        #  y factor weights the delta HR according to blood lactate [cite: 1374]
        y_factor = 1.92 if self.sex == 'male' else 1.67
        
        # TRIMP = mins * HRr * 0.64 * e^(y * HRr) [cite: 1373]
        trimp_step = (dt / 60.0) * hr_reserve_fraction * 0.64 * np.exp(y_factor * hr_reserve_fraction)
        self.cumulative_trimp += trimp_step

    def get_state(self):
        return {"trimp": float(round(self.cumulative_trimp, 3))}

class ClinicalProfile(HeartProfile):
    """ Profile for VitalDB surgical patients with Machine Learning in Rust."""
    def __init__(self):
        self.systemic_stress = 0.0
        self.anesthesia_depth = 0.0
    
    def update_metrics(self, current_hr, resting_hr, max_hr, dt, intensity):
        # Here will go the pathological stress logic in the future
        pass

    def get_state(self):
        return {"clinical_stress": self.systemic_stress}




# PHYSIOLOGICAL MOTOR BASE (The Heart)

class HeartModel:
    def __init__(self, age: int, sex: str, resting_hr: int, max_hr: int = None, profile: HeartProfile = None):
        self.age = age
        self.resting_hr = resting_hr
        self.max_hr = max_hr if max_hr else (220 - age)
        self.current_hr = float(resting_hr)
        self.profile = profile if profile else AthleteProfile(sex)
        
        self.prev_variation = 0.0
        self.is_recovering = False
        self.recovery_start_hr = 0
        self.seconds_since_recovery_start = 0.0
        self.hrr_1min = 0.0
        
        # Short-term memory for Data Science (HRV)
        # Store the last 30 seconds of RR intervals in milliseconds
        self.rr_history = deque(maxlen=30)

    def _get_stochastic_hrv(self):
        age_factor = max(0.2, 1.0 - (self.age / 100))
        phi = 0.8 
        innovation = random.normalvariate(0, 0.5 * age_factor)
        self.prev_variation = (phi * self.prev_variation) + innovation
        return self.prev_variation

    def _calculate_rmssd(self):
        """Calculating the mathematical RMSSD based on the window of the last 30s."""
        if len(self.rr_history) < 2:
            return 0.0
        
        # Array of successive differences
        diffs = [self.rr_history[i] - self.rr_history[i-1] for i in range(1, len(self.rr_history))]
        # Square the differences
        sq_diffs = [d**2 for d in diffs]
        # Square root of the mean
        rmssd = np.sqrt(np.mean(sq_diffs))
        return float(round(rmssd, 2))

    def simulate_step(self, intensity: float, dt: float = 1.0, temperature: float = 20.0, slope_percent: float = 0.0):
        previous_hr = self.current_hr

        slope_impact = (abs(slope_percent) ** 1.5) * 0.015
        if slope_percent < 0:
            effective_intensity = intensity - (slope_impact * 0.5)
        else:
            effective_intensity = intensity + slope_impact

        effective_intensity = max(0.0, min(1.2, effective_intensity))
        target_hr = self.resting_hr + (self.max_hr - self.resting_hr) * effective_intensity

        if temperature > 25.0:
            target_hr += (temperature - 25.0) * 1.2
        
        if target_hr >= self.current_hr:
            tau = 25.0 
        else:
            tau = 5.0 
            
        alpha = 1 - np.exp(-dt / tau)
        self.current_hr += (target_hr - self.current_hr) * alpha

        self.profile.update_metrics(self.current_hr, self.resting_hr, self.max_hr, dt, intensity)
        self._update_recovery_metrics(intensity, dt, previous_hr)

        display_hr = self.current_hr + self._get_stochastic_hrv()
        
        # Translate Heartbeats to RR Intervals (ms) and save in memory
        rr_interval_ms = 60000.0 / max(1.0, display_hr)
        self.rr_history.append(rr_interval_ms)
        
        return self.get_metrics(display_hr)

    def _update_recovery_metrics(self, intensity, dt, previous_hr):
        if intensity < 0.1 and previous_hr > (self.resting_hr + 20) and not self.is_recovering:
            self.is_recovering = True
            self.recovery_start_hr = previous_hr
            self.seconds_since_recovery_start = 0.0
            
        if self.is_recovering:
            self.seconds_since_recovery_start += dt
            if 60.0 <= self.seconds_since_recovery_start <= 60.0 + dt:
                self.hrr_1min = self.recovery_start_hr - self.current_hr
            if intensity > 0.2:
                self.is_recovering = False

    def get_metrics(self, current_hr_display):
        zone_name, zone_color = self._get_training_zone(current_hr_display)
        
        metrics = {
            "bpm": float(round(current_hr_display, 1)),
            "hrr_1min": float(round(self.hrr_1min, 1)),
            "rmssd": self._calculate_rmssd(), 
            "zone": zone_name,
            "color": zone_color  
        }
        metrics.update(self.profile.get_state())
        return metrics

    def _get_training_zone(self, hr):
        percent = hr / self.max_hr
        if percent < 0.6: return "Zone 1 (Very Light)", "#3B82F6"  
        if percent < 0.7: return "Zone 2 (Light)", "#10B981"       
        if percent < 0.8: return "Zone 3 (Moderate)", "#F59E0B"    
        if percent < 0.9: return "Zone 4 (Hard)", "#F97316"        
        return "Zone 5 (Maximum)", "#EF4444"