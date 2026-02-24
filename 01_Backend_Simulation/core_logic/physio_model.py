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
    """Profile for the Kaggle athlete (TRIMP fatigue & Eccentric Load)"""
    def __init__(self, sex: str):
        self.sex = sex.lower()
        self.cumulative_trimp = 0.0
        self.eccentric_load = 0.0  # Accumulator of muscular fatigue due to downhill running

    def update_metrics(self, current_hr, resting_hr, max_hr, dt, intensity, slope_percent=0.0):
        # Calculation of TRIMP Exponential (Banister, 1991) 
        hr_reserve_fraction = (current_hr - resting_hr) / max(1.0, (max_hr - resting_hr))
        hr_reserve_fraction = max(0.0, hr_reserve_fraction)
        
        y_factor = 1.92 if self.sex == 'male' else 1.67
        trimp_step = (dt / 60.0) * hr_reserve_fraction * 0.64 * np.exp(y_factor * hr_reserve_fraction)
        self.cumulative_trimp += trimp_step

        # Calculation of Eccentric Load (Muscular damage due to downhill running)
        # If there is intensity (moving) and the slope is negative (downhill)
        if intensity > 0 and slope_percent < 0:
            # The steeper the slope and the higher the intensity, the greater the eccentric damage
            eccentric_stress = abs(slope_percent) * intensity * (dt / 60.0)
            self.eccentric_load += eccentric_stress

    def get_state(self):
        return {
            "trimp": float(round(self.cumulative_trimp, 3)),
            "eccentric_load": float(round(self.eccentric_load, 3)) 
        }


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
    def __init__(self, age: int, sex: str, resting_hr: int, max_hr: int = None, vo2_max: float = 40.0, profile: HeartProfile = None):
        self.age = age
        self.resting_hr = resting_hr
        self.max_hr = max_hr if max_hr else (208 - 0.7 * age)
        self.vo2_max = vo2_max
        self.current_hr = float(resting_hr)
        self.profile = profile if profile else AthleteProfile(sex)
        
        self.prev_variation = 0.0
        self.is_recovering = False
        self.recovery_start_hr = 0
        self.seconds_since_recovery_start = 0.0
        self.hrr_1min = 0.0
        self.recovery_curve = []
        self.hrrpt_time = 0.0
        
        # Short-term memory for Data Science (HRV)
        # Store the last 30 seconds of RR intervals in milliseconds
        self.rr_history = deque(maxlen=30)

    def _get_stochastic_hrv(self):
        age_factor = max(0.2, 1.0 - (self.age / 100))
        phi = 0.8 
        innovation = random.normalvariate(0, 0.5 * age_factor)
        self.prev_variation = (phi * self.prev_variation) + innovation
        return self.prev_variation


    def _calculate_hrv_metrics(self):
        """Calculate RMSSD, SD1 and SD2 using the Poincaré plot of the HRV."""
        if len(self.rr_history) < 2:
            return 0.0, 0.0, 0.0
        
        rr_array = np.array(self.rr_history)
        diffs = np.diff(rr_array)
        sq_diffs = diffs ** 2
        
        rmssd = np.sqrt(np.mean(sq_diffs))
        
        # SD1: Minor axis of the Poincaré plot (Parasympathetic activity)
        sd1 = rmssd / np.sqrt(2)
        
        # SD2: Major axis (Sympathetic + Parasympathetic activity)
        sdrr = np.std(rr_array)
        sd2_sq = (2 * (sdrr ** 2)) - (sd1 ** 2)
        sd2 = np.sqrt(max(0.0, sd2_sq)) # max() prevents negative values due to rounding
        
        return float(round(rmssd, 2)), float(round(sd1, 2)), float(round(sd2, 2))



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

        self.profile.update_metrics(self.current_hr, self.resting_hr, self.max_hr, dt, intensity, slope_percent)
        self._update_recovery_metrics(intensity, dt, previous_hr)

        display_hr = self.current_hr + self._get_stochastic_hrv()
        
        # Translate Heartbeats to RR Intervals (ms) and save in memory
        rr_interval_ms = 60000.0 / max(1.0, display_hr)
        self.rr_history.append(rr_interval_ms)
        
        return self.get_metrics(display_hr)

    def _update_recovery_metrics(self, intensity, dt, previous_hr):
        # Detect the biggining of the recuperation (low intensity after effort)
        if intensity < 0.1 and previous_hr > (self.resting_hr + 20) and not self.is_recovering:
            self.is_recovering = True
            self.recovery_start_hr = previous_hr
            self.seconds_since_recovery_start = 0.0
            self.recovery_curve = [] # Reset the curve
            
        if self.is_recovering:
            self.seconds_since_recovery_start += dt
            self.recovery_curve.append((self.seconds_since_recovery_start, self.current_hr))

            # Calculate standard HRR at 1 minute
            if 60.0 <= self.seconds_since_recovery_start <= 60.0 + dt:
                self.hrr_1min = self.recovery_start_hr - self.current_hr
            
            # Calculate HRRPT using the maximum perpendicular distance algorithm
            # Based on Bartels et al. (2018). Expect to have enough points (e.g. 30s)
            if len(self.recovery_curve) > 30:
                p_start = np.array(self.recovery_curve[0])
                p_end = np.array(self.recovery_curve[-1])
                
                max_dist = -1
                hrrpt_candidate = 0.0
                
                # Find the farthest point from the straight line between the start and end
                for point in self.recovery_curve:
                    p = np.array(point)
                    # Distance formula from a point to a line
                    dist = np.linalg.norm(np.cross(p_end - p_start, p_start - p)) / np.linalg.norm(p_end - p_start)
                    if dist > max_dist:
                        max_dist = dist
                        hrrpt_candidate = point[0] # The time (seconds) of that point
                
                self.hrrpt_time = hrrpt_candidate

            # If the athlete accelerates again, end in the recovery phase
            if intensity > 0.2:
                self.is_recovering = False


    def get_metrics(self, current_hr_display):
        zone_name, zone_color = self._get_training_zone(current_hr_display)
        rmssd, sd1, sd2 = self._calculate_hrv_metrics() # Llamamos a la nueva función
        
        metrics = {
            "bpm": float(round(current_hr_display, 1)),
            "hrr_1min": float(round(self.hrr_1min, 1)),
            "hrrpt": float(round(self.hrrpt_time, 1)),
            "rmssd": rmssd,
            "sd1": sd1,      
            "sd2": sd2,      
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