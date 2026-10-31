from manim import *
from qiskit import QuantumCircuit, QuantumRegister
from qiskit.circuit.library import QFT
from qiskit.quantum_info import Statevector, partial_trace
import numpy as np

class DraperAddition(Scene):
    def construct(self):
        # --- 1. Qiskit Logic (Pre-compute phases) ---
        def get_b_phases(qc):
            """Extracts phase angles from the statevector, mapping to [0, 2pi)"""
            sv = Statevector(qc)
            b_indices = [4, 5, 6, 7]
            phases = []
            for idx in b_indices:
                other_qubits = [q for q in range(8) if q != idx]
                rho = partial_trace(sv, other_qubits).data
                if np.abs(rho[1, 0]) > 1e-5:
                    phases.append(np.mod(np.angle(rho[1, 0]), 2 * np.pi))
                else:
                    phases.append(0.0)
            return phases

        a = QuantumRegister(4, 'a')
        b = QuantumRegister(4, 'b')
        qc = QuantumCircuit(a, b)

        qc.x(a[0]) 
        qc.x(a[2]) 
        qc.x(b[0]) 
        qc.x(b[1]) 

        discrete_phases = []
        frame_titles = []
        a_bits = [1, 0, 1, 0]

        # Step 0
        qc.append(QFT(4, do_swaps=False).to_gate(label="QFT"), b)
        discrete_phases.append(get_b_phases(qc))
        frame_titles.append("Step 0: Initial QFT (B=3 encoded as phases)")

        # Generate gates and track state
        step = 1
        for j in range(4):           
            for k in range(j + 1):   
                angle = np.pi / (2 ** (j - k))
                qc.cp(angle, a[k], b[j])
                
                discrete_phases.append(get_b_phases(qc))
                if a_bits[k] == 1:
                    frame_titles.append(f"Step {step}: a_{k}=1 -> Shifted b_{j} phase")
                else:
                    frame_titles.append(f"Step {step}: a_{k}=0 -> No shift for b_{j}")
                step += 1

        # --- 2. Manim Scene Setup ---
        title = Text("Quantum Draper Addition: 0101 (5) + 0011 (3) = 1000 (8)", font_size=32, weight=BOLD)
        title.to_edge(UP)
        
        subtitle = Text(frame_titles[0], font_size=24, color=BLUE)
        subtitle.next_to(title, DOWN, buff=0.3)
        
        self.add(title, subtitle)

        clocks = VGroup()
        trackers = []
        
        # Build the phase clocks
        for i in range(4):
            clock_group = VGroup()
            circle = Circle(radius=1.2, color=GRAY)
            
            # Mathematical labels
            l_0 = MathTex("0").scale(0.6).next_to(circle, RIGHT, buff=0.1)
            l_pi2 = MathTex("\\pi/2").scale(0.6).next_to(circle, UP, buff=0.1)
            l_pi = MathTex("\\pi").scale(0.6).next_to(circle, LEFT, buff=0.1)
            l_3pi2 = MathTex("3\\pi/2").scale(0.6).next_to(circle, DOWN, buff=0.1)
            name = MathTex(f"b_{i}").scale(0.8).next_to(circle, DOWN, buff=0.8)
            
            # The value tracker drives the animation mathematically
            tracker = ValueTracker(discrete_phases[0][i])
            trackers.append(tracker)
            
            # The arrow updater ties the vector's position to the tracker's angle
            hand = Arrow(ORIGIN, RIGHT, buff=0, color=YELLOW)
            def update_hand(m, t=tracker, c=circle):
                angle = t.get_value()
                start_pt = c.get_center()
                # 1.15 keeps the arrow tip slightly inside the circle radius
                end_pt = start_pt + np.array([1.15 * np.cos(angle), 1.15 * np.sin(angle), 0])
                m.become(Arrow(start_pt, end_pt, buff=0, color=YELLOW))
            
            hand.add_updater(update_hand)
            
            clock_group.add(circle, l_0, l_pi2, l_pi, l_3pi2, name, hand)
            clocks.add(clock_group)
            
        clocks.arrange(RIGHT, buff=0.8).shift(DOWN * 0.5)
        
        # Initial render
        self.play(FadeIn(clocks))
        self.wait(1)

        # --- 3. Animation Loop ---
        current_phases = discrete_phases[0].copy()
        
        for i in range(1, len(discrete_phases)):
            target_phases = discrete_phases[i]
            new_subtitle = Text(frame_titles[i], font_size=24, color=BLUE).next_to(title, DOWN, buff=0.3)
            
            animations = []
            for j in range(4):
                # Calculate shortest forward rotation
                delta = (target_phases[j] - current_phases[j]) % (2 * np.pi)
                if delta > 1.9 * np.pi:
                    delta = 0.0
                
                new_angle = current_phases[j] + delta
                animations.append(trackers[j].animate.set_value(new_angle))
                current_phases[j] = new_angle
            
            # Transform text while smoothly rotating the clock hands
            animations.append(Transform(subtitle, new_subtitle))
            
            self.play(*animations, run_time=1.0)
            self.wait(0.5) # Pause to let the eye catch the new state
            
        self.wait(2)
