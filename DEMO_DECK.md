# 📊 The Forgetting Engine — Live Demo Slide Deck

*A syllabus-aware, machine-learning-driven memory retention and revision recommendation system.*

---

## Slide 1: Title Slide

### **The Forgetting Engine**
#### *Intelligent Memory Retention Prediction & Syllabus-Aware Revision Queue*
**Course / Track:** Machine Learning Mini Project  
**Team Members:** Nandini & Prisha Gupta  
**Repository:** [github.com/prishagupta17/MLMiniProject](https://github.com/prishagupta17/MLMiniProject)  
**Tech Stack:** Python 3.14 · FastAPI · Scikit-Learn · SQLite · React 18 · Vite · Tailwind CSS  

> **🗣️ Presenter Script (30 seconds):**  
> *"Good morning, Sir. Today we are presenting 'The Forgetting Engine'. It is an end-to-end machine learning system that predicts, for each individual topic a student studies, their real-time probability of forgetting it, and automatically builds a calm, prioritized revision schedule before their exams."*

---

## Slide 2: The Problem

### **The Revision Dilemma in Higher Education**
* **The Forgetting Curve (Ebbinghaus, 1885)**: Memory retention decays exponentially over time without structured spaced reinforcement.
* **Why Traditional Revision Fails**:
  * Students suffer from the **Illusion of Competence** — revising what feels easy rather than what is fading.
  * Cramming right before exams creates short-term recall with near-zero long-term retention.
* **The Gap in Current Tools (Anki, SuperMemo)**:
  * Flashcard apps are syllabus-agnostic.
  * They ignore topic prerequisites, lecture hierarchies, upcoming exam schedules, and cognitive study overload.

> **🗣️ Presenter Script (45 seconds):**  
> *"Sir, cognitive science has proven that human memory decays exponentially if left unreviewed. However, when university students sit down to study, they face a classic dilemma: they either revise what is familiar because it feels comfortable, or they cram everything in the final 48 hours before an exam. Existing tools like Anki only operate on isolated flashcards; they know nothing about course syllabi, lecture dependencies, or exam dates. We wanted to build a syllabus-aware machine learning engine that bridges this gap."*

---

## Slide 3: Our Solution

### **The Forgetting Engine Concept**
* **Syllabus Ground Truth**: Ingests real course curricula (156 topics across 4 engineering courses, 21 modules, 20 scheduled assessments).
* **Dynamic Student Tracking**: Captures self-reported study duration, revision cadence, and self-check quiz outcomes.
* **Real-Time ML Inference**: Calculates forgetting probability $P(\text{forgot}) \in [0.0, 1.0]$ on the fly.
* **Cognitive Load-Conscious UI**: Renders a calm, non-overwhelming single focus topic with clear risk tiers:
  * 🟢 **Remembered** ($P < 35\%$)
  * 🟡 **Review Soon** ($35\% \le P < 60\%$)
  * 🔴 **Needs Refresher** ($P \ge 60\%$)

> **🗣️ Presenter Script (45 seconds):**  
> *"Our solution parses actual university curricula directly into SQLite. Every time a student logs study time or tests their recall, our engine recalculates their personal forgetting probability for that topic. Instead of overwhelming students with complex charts, the interface gives them a single top-priority focus topic, categorized cleanly into Remembered, Review Soon, or Needs Refresher."*

---

## Slide 4: System Architecture

### **End-to-End 3-Tier Architecture**

```
┌────────────────────────────────────────────────────────┐
│             FRONTEND (React + Vite + Tailwind)         │
│  - Dashboard (Focus Topic + Up Next)                   │
│  - My Courses (156 topics across 4 courses)            │
│  - Study Planner (High / Moderate priority backlogs)   │
│  - Progress Tracker (Retention breakdown)              │
└───────────────────────────┬────────────────────────────┘
                            │ REST API calls (/api proxy)
┌───────────────────────────▼────────────────────────────┐
│                  BACKEND (FastAPI + Python)            │
│  - Curriculum & Event Management                       │
│  - Dynamic 13-Feature Extraction (Zero Leakage)        │
│  - Real-time ML Inference Engine                       │
│  - Log-Odds Local Explainability Module                │
└──────────────┬──────────────────────────┬──────────────┘
               │                          │
┌──────────────▼──────────┐  ┌────────────▼──────────────┐
│       SQLite DB         │  │    Machine Learning Model │
│  - 9 Relational Tables  │  │  - Scikit-Learn .joblib   │
│  - Topics & Assessments │  │  - Balanced Logistic Reg. │
│  - Study Logs & Quizzes │  │  - StandardScaler Pipeline│
└─────────────────────────┘  └───────────────────────────┘
```

> **🗣️ Presenter Script (45 seconds):**  
> *"Here is our system architecture. The frontend is built with React and Vite using Tailwind CSS. It communicates via a REST API with our FastAPI backend. The backend manages our SQLite database containing 9 relational tables. Whenever the frontend requests the dashboard, the backend queries the student's study events, extracts 13 dynamic features, feeds them through our Scikit-Learn model bundle, and returns the sorted predictions."*

---

## Slide 5: Machine Learning & Feature Engineering

### **13 Features with Zero Label Leakage**

| Category | Feature Name | Description |
|---|---|---|
| **Recency & Pacing** | `days_since_last_studied` | Days elapsed since the student's last review. |
| | `times_studied` | Cumulative count of study sessions on this topic. |
| | `is_first_exposure` | Binary indicator for first-time exposure. |
| | `revision_frequency` | Pacing of revisions over the learning window. |
| **Effort & Confidence** | `time_spent_studying_min` | Total cumulative minutes logged studying. |
| | `self_reported_confidence`| Average subjective confidence (0.0 to 1.0). |
| **Curriculum Context** | `universal_difficulty` | Seeded syllabus difficulty rating. |
| | `topic_importance` | Exam coverage weight across midterms/finals. |
| | `confusability_score` | Count of confusable sibling concepts. |
| | `prerequisite_completion_ratio` | Fraction of required prerequisite topics studied. |
| **Cognitive Load & Exams**| `concurrent_topic_load` | Distinct other topics studied in the last 7 days. |
| | `days_to_next_assessment`| Days until the next covering exam (capped at 60). |
| | `has_upcoming_assessment`| Binary flag for an approaching exam. |

> **Strict Zero-Leakage Guarantee**: Self-check quiz results (`RecallEvent.is_correct`) serve **only as training labels**, never as model input features.

> **🗣️ Presenter Script (60 seconds):**  
> *"Our machine learning model uses 13 features capturing four dimensions: recency, effort, curriculum structure, and cognitive load. For example, `concurrent_topic_load` penalizes cramming 20 different topics in a single week, while `prerequisite_completion_ratio` accounts for whether foundational concepts were mastered first. Most importantly, we enforce a strict zero label-leakage rule: recall check correctness is used solely as the target label during training and never leaked into the input feature vector."*

---

## Slide 6: Model Selection & Explainability

### **Why Balanced Logistic Regression?**

* **Probability Calibration**: Outputs smooth, reliable probabilities $P \in [0, 1]$ via the sigmoid function.
* **Handling Class Imbalance**: Uses `class_weight="balanced"` to prevent majority-class bias.
* **Exact Mathematical Explainability**:
  Unlike black-box models (e.g., Random Forests or Neural Networks), Logistic Regression allows an **exact log-odds linear decomposition**:

$$\text{intercept} + \sum_{i=1}^{13} (\beta_i \cdot \tilde{x}_i) = \text{predicted log-odds} = z$$
$$P(\text{forgot}) = \frac{1}{1 + e^{-z}}$$

* **Top Learned Model Weights**:
  * **Strongest Memory Preserver**: `times_studied` ($\beta = -0.4527$) — More spaced repetitions drastically lower risk.
  * **Strongest Risk Driver**: `days_since_last_studied` ($\beta = +0.4283$) — Time elapsed without review is the primary driver of forgetting.

> **🗣️ Presenter Script (60 seconds):**  
> *"We benchmarked Logistic Regression against Random Forests and chose Balanced Logistic Regression. It not only produces calibrated probabilities, but also allows exact mathematical explainability. Because it operates in linear log-odds space, we can break down the exact signed contribution of every single feature. The model's top learned weights directly mirror cognitive psychology: `times_studied` is the strongest protector of memory, while `days_since_last_studied` is the strongest driver of forgetting."*

---

## Slide 7: Live Demonstration (Switch to Screen)

### **Interactive Demo Workflow**

1. **Verification Test Suite**: Run `pytest tests/ -q` $\rightarrow$ Show **53/53 tests passing**.
2. **Interactive API Documentation**: Open `http://127.0.0.1:8000/docs` $\rightarrow$ Show FastAPI Swagger endpoints.
3. **Student Dashboard**: Open `http://localhost:3000` $\rightarrow$ Show student view, risk counters, and Focus Topic.
4. **Live Study Logging**: 
   * Navigate to an unstudied topic in *My Courses*.
   * Click **Study**, input **45 minutes** with **85% confidence**, and click **Save**.
   * Return to Dashboard $\rightarrow$ Show immediate dynamic probability recalculation!
5. **Study Planner**: Show how topics $\ge 60\%$ automatically populate *Immediate Priority*.

> **🗣️ Presenter Script (Transition to live screen):**  
> *"Now, Sir, let us demonstrate the live running code on our system..."* *(Follow the 4-step live demo steps).*

---

## Slide 8: Verification & Test Suite

### **Testing & Model Governance**

* **Pytest Suite**: **53 passed tests** across 6 distinct modules:
  * `test_seed_ground_truth.py`: Curriculum integrity (156 topics, 20 assessments).
  * `test_seed_loader.py`: Seed loading idempotency.
  * `test_step2_features.py`: Zero label leakage and dynamic feature boundaries.
  * `test_step3_simulation.py`: Simulated student generation across 6 behavioural archetypes.
  * `test_step4_explanations.py`: Mathematical verification of log-odds identity.
  * `test_model_v2.py`: Model bundle schema compatibility and `log1p` bounds.
* **Frozen Model Artifacts**:
  * Production: `forgetting_model.joblib` (SHA-256: `4F0862C7D7FB33AC`).
  * Experimental Candidate v2: `forgetting_model_v2.joblib` (SHA-256: `03E89030D3F79526`).

> **🗣️ Presenter Script (45 seconds):**  
> *"Our project follows rigorous software engineering and model governance practices. We have 53 automated tests ensuring that the syllabus ground truth is valid, that no target leakage occurs, and that the mathematical decomposition holds up to machine precision. Our production model artifact is cryptographically frozen with SHA-256 verification."*

---

## Slide 9: Limitations & Future Enhancements

### **Honest Engineering Limitations & Roadmap**

* **Current Limitations**:
  * **Simulation Training**: Trained on simulated cohorts; benefits from ongoing tuning as real-world student data accumulates.
  * **Local In-Memory Cache**: Uses SQLite for rapid local deployment; production scaling would migrate to PostgreSQL.
  * **Single Global Model**: Currently one global weight vector; does not yet use personalized per-student random effects.
* **Future Roadmap**:
  * **Bayesian Personalized Priors**: Incorporate student-specific learning rate priors.
  * **LMS Integration**: Connect via Canvas / Moodle LTI to automatically pull real assignment deadlines.
  * **Adaptive Flashcard Hybridization**: Combine syllabus-level topic risk with flashcard-level FSRS (Free Spaced Repetition Scheduler).

> **🗣️ Presenter Script (40 seconds):**  
> *"In terms of limitations and next steps: the initial model was trained on simulated student trajectories modeled after Ebbinghaus decay curves. As real study data accumulates, we can apply online learning or Bayesian hierarchical modeling to personalize weights per student. Additionally, integrating this with campus LMS systems like Canvas would allow automatic syncing of assignment deadlines."*

---

## Slide 10: Conclusion & Q&A

### **Summary of Contributions**

1. **Syllabus-Aware**: Grounded in real university engineering curricula with prerequisite dependencies.
2. **Zero-Leakage ML Pipeline**: 13 cognitive features evaluated in real time without target contamination.
3. **Calm, Student-First Design**: Reduces exam anxiety by turning a chaotic semester into a single focus topic.
4. **Transparent & Tested**: Fully explainable log-odds mathematics backed by a 53-test verification suite.

---

### **Thank You!**
**Questions & Discussion**

> **🗣️ Presenter Script (20 seconds):**  
> *"To summarize: The Forgetting Engine turns the overwhelming stress of exam preparation into a clear, scientifically grounded daily revision queue. Thank you, Sir. We would be happy to take your questions."*
