import numpy as np
import random

class HeartModel:
    def __init__(self, age: int, sex: str, resting_hr: int, max_hr: int = None):
        """
        Based on: 
        - Neuroanatomy, Parasympathetic/Sympathetic Nervous System [cite: 11, 453]
        - Banister's TRIMP Formula [cite: 372, 1027]
        """
        self.age = age
        self.sex = sex.lower()  # 'male' or 'female' for Banister's 'y' factor [cite: 381]
        self.resting_hr = resting_hr
        self.max_hr = max_hr if max_hr else (220 - age)
        
        # Dynamic state
        self.current_hr = float(resting_hr)
        self.cumulative_trimp = 0.0
        
        # HRV variables (chaotic modeling/variability) [cite: 1144, 1162]
        self.prev_variation = 0.0
        
        # Bifasic recovery logic [cite: 850, 852]
        self.is_recovering = False
        self.recovery_start_hr = 0
        self.seconds_since_recovery_start = 0.0
        self.hrr_1min = 0.0

    def _get_stochastic_hrv(self):
        """
        A healthy heart is not a metronome; it's a chaotic system[cite: 1144, 1162].
        Simulate variability dependent on state (simple pink noise).
        """
        # Variability decreases with age[cite: 52, 1423].
        age_factor = max(0.2, 1.0 - (self.age / 100))
        # Process of Gauss-Markov to give 'memory' to the heartbeat.
        phi = 0.8 
        innovation = random.normalvariate(0, 0.5 * age_factor)
        self.prev_variation = (phi * self.prev_variation) + innovation
        return self.prev_variation

    def simulate_step(self, intensity: float, dt: float = 1.0, temperature: float = 20.0, slope_percent: float = 0.0):
        """
        Advance the simulation integrating the SNA response.
        """
        previous_hr = self.current_hr

        # Logic of Terrain No-lineal (STEP 0)
        # Use power 1.5: the cost grows faster than the slope.
        # The factor 0.015 calibrates that a 10% slope is a serious but not mortal effort.
        slope_impact = (abs(slope_percent) ** 1.5) * 0.015
        
        # If the slope is negative (downhill), the effort goes down, 
        # but only 50% of what it would go up (eccentric braking).
        if slope_percent < 0:
            effective_intensity = intensity - (slope_impact * 0.5)
        else:
            effective_intensity = intensity + slope_impact

        # Limit the intensity between 0 (rest) and 1.2 (overexertion)
        effective_intensity = max(0.0, min(1.2, effective_intensity))
        
        # 1. Calculation of Heart Rate Reserve (HRR) [cite: 379, 1070]
        # Target HR based on intensity
        target_hr = self.resting_hr + (self.max_hr - self.resting_hr) * effective_intensity

        # 2. Temperature Adjustment (Thermoregulation)
        if temperature > 25.0:
            target_hr += (temperature - 25.0) * 1.2
        
        # 3. Autonomic Asymmetry: The sympathetic nervous system is slower than the parasympathetic nervous system.
        # Tau (time constant) in seconds.
        if target_hr >= self.current_hr:
            # Sympathetic Response (slow: >5s) 
            tau = 20.0 
        else:
            # Parasympathetic Response (fast: <1s) [cite: 1207, 1322]
            tau = 100.0 
            
        alpha = 1 - np.exp(-dt / tau)
        self.current_hr += (target_hr - self.current_hr) * alpha

        # 4. Calculation of TRIMP Exponential (Banister, 1991) [cite: 375, 1072]
        # HRr = (HR_actual - HR_reposo) / (HR_max - HR_reposo)
        hr_reserve_fraction = (self.current_hr - self.resting_hr) / (self.max_hr - self.resting_hr + 0.0001)
        hr_reserve_fraction = max(0, hr_reserve_fraction)
        
        # y factor: 1.92 for men, 1.67 for women 
        y_factor = 1.92 if self.sex == 'male' else 1.67
        
        # TRIMP = mins * HRr * 0.64 * e^(y * HRr) [cite: 1072]
        # dt/60 for minutes
        trimp_step = (dt / 60.0) * hr_reserve_fraction * 0.64 * np.exp(y_factor * hr_reserve_fraction)
        self.cumulative_trimp += trimp_step

        # 5. Management of Bifasic Recovery [cite: 850, 852]
        self._update_recovery_metrics(intensity, dt, previous_hr)

        # 6. Inject Realistic Variability (HRV) [cite: 1143, 1159]
        display_hr = self.current_hr + self._get_stochastic_hrv()
        
        return self.get_metrics(display_hr)

    def _update_recovery_metrics(self, intensity, dt, previous_hr):
        """
        Detects the fast (PNS) and slow (SNS) recovery phases.
        """
        if intensity < 0.1 and previous_hr > (self.resting_hr + 20) and not self.is_recovering:
            self.is_recovering = True
            self.recovery_start_hr = previous_hr
            self.seconds_since_recovery_start = 0.0
            
        if self.is_recovering:
            self.seconds_since_recovery_start += dt
            # Measure HRR at 1 minute (Cleveland Clinic Standard) [cite: 133, 153]
            if 60.0 <= self.seconds_since_recovery_start <= 60.0 + dt:
                self.hrr_1min = self.recovery_start_hr - self.current_hr
            
            if intensity > 0.2: # Interrupt if returns to exercise
                self.is_recovering = False

    def get_metrics(self, current_hr_display):
        zone_name, zone_color = self._get_training_zone(current_hr_display)
        return {
            "bpm": float(round(current_hr_display, 1)),
            "trimp": float(round(self.cumulative_trimp, 3)),
            "hrr_1min": float(round(self.hrr_1min, 1)),
            "zone": zone_name,
            "color": zone_color  
        }

    def _get_training_zone(self, hr):
        """Based on the 5 training zones and Karvonen formula"""
        percent = hr / self.max_hr
        
        if percent < 0.6: 
            return "Zone 1 (Very Light)", "#3B82F6"  
        if percent < 0.7: 
            return "Zone 2 (Light)", "#10B981"       
        if percent < 0.8: 
            return "Zone 3 (Moderate)", "#F59E0B"    
        if percent < 0.9: 
            return "Zone 4 (Hard)", "#F97316"        
        
        return "Zone 5 (Maximum)", "#EF4444"         