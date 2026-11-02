"""
Generates the 4 verified seed JSON files according to the ground truth and Step 2 specification.
"""
import os
import json

os.makedirs("backend/seed", exist_ok=True)

# 1. ML (CSE 3148)
ml_data = {
    "course_info": {
        "code": "CSE 3148",
        "name": "Machine Learning",
        "credits": 4,
        "semester": "Odd",
        "academic_year": "2026-2027"
    },
    "outcomes": [
        {"code": "CO1", "statement": "Apply basic concepts of Statistical Learning", "hours": 15, "marks": 22},
        {"code": "CO2", "statement": "Apply Linear Regression and classification", "hours": 26, "marks": 35},
        {"code": "CO3", "statement": "Use decision trees for classification", "hours": 11, "marks": 15},
        {"code": "CO4", "statement": "Use support vector machines for classification and regression", "hours": 10, "marks": 14},
        {"code": "CO5", "statement": "Apply unsupervised learning methods for clustering", "hours": 10, "marks": 14}
    ],
    "lesson_plan": [
        {"lecture_num": 1, "name": "An Overview of Statistical Learning, A Brief History of Statistical Learning, Notation and Simple Matrix Algebra", "co_code": "CO1"},
        {"lecture_num": 2, "name": "Statistical Learning: What is Statistical Learning?, Why Estimate f ?, How Do We Estimate f ?", "co_code": "CO1"},
        {"lecture_num": 3, "name": "Parametric Methods and Non- Parametric Methods", "co_code": "CO1"},
        {"lecture_num": 4, "name": "The Trade-Off Between Prediction Accuracy and Model Interpretability, Supervised Versus Unsupervised Learning, Regression Versus Classification Problems", "co_code": "CO1"},
        {"lecture_num": 5, "name": "Assessing Model Accuracy, Measuring the Quality of Fit, The Bias-Variance Trade-Off", "co_code": "CO1"},
        {"lecture_num": 6, "name": "The Classification Setting, The Bayes Classifier, K-NearestNeighbors [Overfit, Underfit]", "co_code": "CO1"},
        {"lecture_num": 7, "name": "Linear Regression: Simple Linear Regression, Estimating the Coefficients, Assessing the Accuracy of the Model, Problem on Simple Linear Regression", "co_code": "CO2"},
        {"lecture_num": 8, "name": "Normal Method, Gradient Descent Method, Normal Equation Method vs Gradient Descent Method", "co_code": "CO2"},
        {"lecture_num": 9, "name": "R2 Statistic, Multiple Linear Regression, Some Important Questions, Problems on Multiple Linear Regression", "co_code": "CO2"},
        {"lecture_num": 10, "name": "One: Is There a Relationship Between the Response and Predictors?, Two: Deciding on Important Variables, Three: Model Fit, Four: Predictions", "co_code": "CO2"},
        {"lecture_num": 11, "name": "Other Considerations in the Regression Model: Qualitative Predictors, Predictors with Only Two Levels, Qualitative Predictors with More than Two Levels", "co_code": "CO2"},
        {"lecture_num": 12, "name": "Extensions of the Linear Model, Removing the Additive Assumption, Non-linear Relationships, Problems on Non-linear Relationships -Polynomial", "co_code": "CO2"},
        {"lecture_num": 13, "name": "Classification: An Overview of Classification, Why Not Linear Regression?, Logistic Regression, Sigmoid Function, Problems on Logistic Regression", "co_code": "CO2"},
        {"lecture_num": 14, "name": "The Logistic Model, Estimating the Regression Coefficients, Making Predictions, Multinomial Logistic Regression", "co_code": "CO2"},
        {"lecture_num": 15, "name": "Cost Function, STOCHASTIC GRADIENT DESCENT", "co_code": "CO2"},
        {"lecture_num": 16, "name": "Performance metrics: Confusion Matrix, Precision and Recall & ROC curve", "co_code": "CO2"},
        {"lecture_num": 17, "name": "BAYESIAN REASONING: Bayes Theorem and Problems, Naive Bayes Classifier", "co_code": "CO2"},
        {"lecture_num": 18, "name": "K-Nearest Neighbour Classifier, Comparison of Linear Regression with K-Nearest Neighbors", "co_code": "CO2"},
        {"lecture_num": 19, "name": "Well-posed machine learning problems, examples of applications indiverse fields", "co_code": "CO3"},
        {"lecture_num": 20, "name": "Data representation: Time Series Forecasting, Datasets for Toy (Unrealistically Simple) and Realistic Problems", "co_code": "CO3"},
        {"lecture_num": 21, "name": "Tree-Based Methods: The Basics of Decision Trees, Example of a Classification", "co_code": "CO3"},
        {"lecture_num": 22, "name": "DECISION TREES: Introduction, Example of a Classification Decision Tree", "co_code": "CO3"},
        {"lecture_num": 23, "name": "ID3, C4.5", "co_code": "CO3"},
        {"lecture_num": 24, "name": "CART Decision Trees", "co_code": "CO3"},
        {"lecture_num": 25, "name": "Pruning the Tree, Strengths and Weaknesses of Decision Tree Approach", "co_code": "CO3"},
        {"lecture_num": 26, "name": "Unsupervised Learning: The Challenge of Unsupervised Learning, Principal Components Analysis", "co_code": "CO5"},
        {"lecture_num": 27, "name": "Applications of PCA, Computing PCA, Problems", "co_code": "CO5"},
        {"lecture_num": 28, "name": "Missing Values and Matrix Completion", "co_code": "CO5"},
        {"lecture_num": 29, "name": "Clustering Methods, K-Means Clustering, Problems", "co_code": "CO5"},
        {"lecture_num": 30, "name": "Hierarchical Clustering, Problems", "co_code": "CO5"},
        {"lecture_num": 31, "name": "Practical Issues in Clustering", "co_code": "CO5"},
        {"lecture_num": 32, "name": "Support Vector Machines: Maximal Margin Classifier- What Is a Hyperplane?, Classification Using a Separating Hyperplane", "co_code": "CO4"},
        {"lecture_num": 33, "name": "The Maximal Margin Classifier, Construction of the Maximal Margin Classifier", "co_code": "CO4"},
        {"lecture_num": 34, "name": "Support Vector Classifiers-Overview of the Support Vector Classifier, Details of the Support Vector Classifier Numerical examples", "co_code": "CO4"},
        {"lecture_num": 35, "name": "Support Vector Machines-Classification with Non-Linear Decision Boundaries, The Support Vector Machine, An Application to the Heart Disease Data Numerical examples", "co_code": "CO4"},
        {"lecture_num": 36, "name": "Rationale, Generating Diverse Learners, Voting, Error-Correcting Output Codes, Bagging, Boosting", "co_code": "CO5"}
    ],
    "lab_weeks": [
        {"week": 1, "topic": "Working with numpy, scipy, and CSV file format", "co_code": "CO1"},
        {"week": 2, "topic": "Data Analysis and visualisation with Python", "co_code": "CO1"},
        {"week": 3, "topic": "Data-Preprocessing and Regression Techniques", "co_code": "CO1"},
        {"week": 4, "topic": "Parametric methods", "co_code": "CO2"},
        {"week": 5, "topic": "LOGISTIC REGRESSION AND STOCHASTIC GRADIENT DESCENT", "co_code": "CO2"},
        {"week": 6, "topic": "Cost Function", "co_code": "CO2"},
        {"week": 7, "topic": "Naïve Bayes Classifier", "co_code": "CO2"},
        {"week": 8, "topic": "K-Nearest Neighbour classifier", "co_code": "CO2"},
        {"week": 9, "topic": "Decision Tree - C4.5 and CART", "co_code": "CO3"},
        {"week": 10, "topic": "Data Clustering K-means and hierarchical", "co_code": "CO5"},
        {"week": 11, "topic": "Support Vector Machine", "co_code": "CO4"},
        {"week": 12, "topic": "Mini-project", "co_code": "CO3"}
    ],
    "sdl_items": [
        {"sl_no": 1, "topic": "Machine Learning With Python", "hours": 8, "co_code": "CO1"},
        {"sl_no": 2, "topic": "Machine Learning Foundations Course – Regression Analysis", "hours": 6, "co_code": "CO2"},
        {"sl_no": 3, "topic": "Stochastic Gradient Descent", "hours": 4, "co_code": "CO2"},
        {"sl_no": 4, "topic": "Generative Models for Classification", "hours": 4, "co_code": "CO2"},
        {"sl_no": 5, "topic": "Principal Component Analysis", "hours": 4, "co_code": "CO2"},
        {"sl_no": 6, "topic": "Naive Bayes Case Studies", "hours": 4, "co_code": "CO2"},
        {"sl_no": 7, "topic": "K-Nearest Neighbors (K-NN) Case Studies", "hours": 4, "co_code": "CO2"},
        {"sl_no": 7, "topic": "Decision Tree Case Studies", "hours": 4, "co_code": "CO3"},
        {"sl_no": 8, "topic": "Support Vector Machine (SVM) case studies", "hours": 4, "co_code": "CO4"},
        {"sl_no": 9, "topic": "Clustering (K-Means, Hierarchical Clustering, DBSCAN) case studies", "hours": 4, "co_code": "CO5"},
        {"sl_no": 10, "topic": "COMBINING MULTIPLE LEARNERS: Rationale, Generating Diverse Learners, Voting, Bagging, Boosting", "hours": 2, "co_code": "CO5"}
    ],
    "sdl_hours_printed_total": 48,
    "assessments": [
        {
            "name": "IA1",
            "type": "Quiz",
            "marks": 5.0,
            "schedule": "17-29 Aug 2026",
            "start_date": "2026-08-17",
            "end_date": "2026-08-29",
            "covered_lectures": list(range(1, 37)),
            "coverage_assumed": True
        },
        {
            "name": "IA2",
            "type": "Quiz",
            "marks": 5.0,
            "schedule": "7-21 Sep 2026",
            "start_date": "2026-09-07",
            "end_date": "2026-09-21",
            "covered_lectures": list(range(1, 37)),
            "coverage_assumed": True
        },
        {
            "name": "Mid-Term",
            "type": "Descriptive",
            "marks": 30.0,
            "schedule": None,
            "start_date": None,
            "end_date": None,
            "covered_lectures": list(range(1, 37)),
            "coverage_assumed": True
        },
        {
            "name": "IA3",
            "type": "Quiz",
            "marks": 5.0,
            "schedule": "19-31 Oct 2026",
            "start_date": "2026-10-19",
            "end_date": "2026-10-31",
            "covered_lectures": list(range(1, 37)),
            "coverage_assumed": True
        },
        {
            "name": "End-Sem",
            "type": "Descriptive",
            "marks": 50.0,
            "schedule": None,
            "start_date": None,
            "end_date": None,
            "covered_lectures": list(range(1, 37)),
            "coverage_assumed": True
        }
    ]
}

# 2. PCAP (CSE 3129)
pcap_data = {
    "course_info": {
        "code": "CSE 3129",
        "name": "Parallel Computer Architecture and Programming",
        "credits": 4,
        "semester": "V",
        "academic_year": "2026-2027"
    },
    "outcomes": [
        {"code": "CO1", "statement": "Demonstrate a fundamental understanding of architecture-level support for parallelization and programming paradigms", "hours": 5, "marks": 14},
        {"code": "CO2", "statement": "Design and implement shared memory programs using OpenMP", "hours": 6, "marks": 17},
        {"code": "CO3", "statement": "Design and implement distributed memory programs using MPI", "hours": 6, "marks": 17},
        {"code": "CO4", "statement": "Design and construct CUDA programs using GPU architecture", "hours": 10, "marks": 27},
        {"code": "CO5", "statement": "Design optimized parallel solutions using thread and memory organization in CUDA", "hours": 9, "marks": 20},
        {"code": "CO6", "statement": "Applying Parallel Programming Concepts to Applications", "hours": None, "marks": 5}
    ],
    "lesson_plan": [
        {"lecture_num": 1, "name": "Introduction to Parallel Computing : Need of Parallelism; Forms of Parallelism, Flynn's taxonomy: SISD, SIMD, MISD, MIMD", "co_code": "CO1"},
        {"lecture_num": 2, "name": "Moore's Law and Multicore; Amdahl's Law", "co_code": "CO1"},
        {"lecture_num": 3, "name": "Speedup and performance; Programming paradigms: Comparison between Shared and Distributed Memory Programming Paradigms", "co_code": "CO1"},
        {"lecture_num": 4, "name": "Introduction to Parallel Random Access Machine (PRAM) Architecture Model: Characteristics of PRAM Models; Types of PRAM Models", "co_code": "CO1"},
        {"lecture_num": 5, "name": "Introduction to Parallel Random Access Machine (PRAM) Architecture Model: Advantages and Limitations of PRAM Models", "co_code": "CO1"},
        {"lecture_num": 6, "name": "Shared Memory Programming Using OpenMP: Introduction to OpenMP: What is OpenMP?, Shared-memory programming: Advantages and limitations, OpenMP programming model", "co_code": "CO2"},
        {"lecture_num": 7, "name": "Fork-join execution and thread-based parallelism, Compiling OpenMP Programs: Enabling OpenMP and Running programs, OpenMP Compiler Directives: parallel, for, sections, single, master", "co_code": "CO2"},
        {"lecture_num": 8, "name": "Data Sharing: Shared variables; Private variables; firstprivate; lastprivate; reduction", "co_code": "CO2"},
        {"lecture_num": 9, "name": "Synchronization: Barrier; Critical sections; Atomic operations. Runtime Functions: omp_get_thread_num(); omp_get_num_threads(); omp_set_num_threads(); omp_get_wtime(). Environment Variables: OMP_NUM_THREADS; OMP_SCHEDULE; OMP_DYNAMIC", "co_code": "CO2"},
        {"lecture_num": 10, "name": "Work Sharing: for directive; sections; single; Combined Parallel and Work-sharing constructs", "co_code": "CO2"},
        {"lecture_num": 11, "name": "Scheduling (static, dynamic, guided)", "co_code": "CO2"},
        {"lecture_num": 12, "name": "Distributed Memory Programming Using MPI: Message-Passing Programming, MPI Basics and Introduction to Distributed-Memory Architectures", "co_code": "CO3"},
        {"lecture_num": 13, "name": "Foundational Concepts of the MPI Standard; Compiling and Running MPI Programs", "co_code": "CO3"},
        {"lecture_num": 14, "name": "Point-to-Point Communication: Send/Recv Between Two Processes; Synchronous and Buffered Send", "co_code": "CO3"},
        {"lecture_num": 15, "name": "Collective Communication: Broadcast, Scatter, Gather and Reduce Operations", "co_code": "CO3"},
        {"lecture_num": 16, "name": "Collective Data Movement and Reduction; Introduction to Allgather and Alltoall", "co_code": "CO3"},
        {"lecture_num": 17, "name": "Measuring the Execution Time of MPI Programs; MPI Error-Handling Functions", "co_code": "CO3"},
        {"lecture_num": 18, "name": "Accelerated Programming Using GPU: GPU Architecture-Transition from CPU to GPU", "co_code": "CO4"},
        {"lecture_num": 19, "name": "Architecture of a Modern GPU", "co_code": "CO4"},
        {"lecture_num": 20, "name": "CUDA Program Structure and Vector-Vector Addition", "co_code": "CO4"},
        {"lecture_num": 21, "name": "Device Global Memory and Data Transfer", "co_code": "CO4"},
        {"lecture_num": 22, "name": "CUDA Kernel Functions and Threads", "co_code": "CO4"},
        {"lecture_num": 23, "name": "CUDA Thread Organization", "co_code": "CO4"},
        {"lecture_num": 24, "name": "Assigning Resources to Blocks and Querying Device Properties", "co_code": "CO4"},
        {"lecture_num": 25, "name": "Sequential and Parallel 1D Convolution", "co_code": "CO4"},
        {"lecture_num": 26, "name": "Sequential Sparse Matrix-Vector Multiplication and Parallel SpMV Using CSR", "co_code": "CO4"},
        {"lecture_num": 27, "name": "CUDA Atomic and Arithmetic Functions", "co_code": "CO4"},
        {"lecture_num": 28, "name": "High-Performance GPU Programming Using Optimizations: Introduction to GPU Performance Optimization", "co_code": "CO5"},
        {"lecture_num": 29, "name": "Mapping Threads to Multidimensional Data", "co_code": "CO5"},
        {"lecture_num": 30, "name": "Matrix-Matrix Multiplication: A More Complex CUDA Kernel", "co_code": "CO5"},
        {"lecture_num": 31, "name": "Synchronization and Transparent Scalability", "co_code": "CO5"},
        {"lecture_num": 32, "name": "CUDA Device Memory Types; Constant Memory and Caching", "co_code": "CO5"},
        {"lecture_num": 33, "name": "Tiled 1D Convolution with Halo Elements", "co_code": "CO5"},
        {"lecture_num": 34, "name": "Importance of Memory-Access Efficiency", "co_code": "CO5"},
        {"lecture_num": 35, "name": "Reducing Global-Memory Traffic and Tiled Matrix-Matrix Multiplication", "co_code": "CO5"},
        {"lecture_num": 36, "name": "Thread Scheduling and Latency Tolerance", "co_code": "CO5"}
    ],
    "sdl_items": [
        {"sl_no": 1, "topic": "Introduction to Parallel Computing - Taxonomy & multicore evolution", "hours": 3, "co_code": "CO1"},
        {"sl_no": 2, "topic": "Performance Analysis - Amdahl's Law & Gustafson's Law", "hours": 3, "co_code": "CO1"},
        {"sl_no": 3, "topic": "Programming Paradigms - OpenMP, MPI, and CUDA comparison", "hours": 3, "co_code": "CO1"},
        {"sl_no": 4, "topic": "Introduction to OpenMP - Install and sample programs", "hours": 3, "co_code": "CO2"},
        {"sl_no": 5, "topic": "Data Sharing and Synchronization in OpenMP", "hours": 3, "co_code": "CO2"},
        {"sl_no": 6, "topic": "Scheduling and Runtime Functions in OpenMP", "hours": 3, "co_code": "CO2"},
        {"sl_no": 7, "topic": "MPI Basics - OpenMPI & Hello World", "hours": 3, "co_code": "CO3"},
        {"sl_no": 8, "topic": "Point-to-Point Communication in MPI", "hours": 3, "co_code": "CO3"},
        {"sl_no": 9, "topic": "Collective Communication in MPI", "hours": 3, "co_code": "CO3"},
        {"sl_no": 10, "topic": "GPU Architecture - Streaming multiprocessors & CUDA cores", "hours": 3, "co_code": "CO4"},
        {"sl_no": 11, "topic": "CUDA Programming Basics - Vector addition & toolkit setup", "hours": 3, "co_code": "CO4"},
        {"sl_no": 12, "topic": "Memory Management in CUDA - Host-device transfer", "hours": 3, "co_code": "CO4"},
        {"sl_no": 13, "topic": "GPU Memory Optimization - Shared vs global memory", "hours": 3, "co_code": "CO5"},
        {"sl_no": 14, "topic": "Warp Execution and Thread Organization in CUDA", "hours": 3, "co_code": "CO5"},
        {"sl_no": 15, "topic": "Memory Optimization using Tiling - Matrix multiplication", "hours": 3, "co_code": "CO5"},
        {"sl_no": 16, "topic": "Parallel Programming Case Study / Mini Project", "hours": 9, "co_code": "CO6"}
    ],
    "sdl_hours_total": 54,
    "assessments": [
        {
            "name": "Mid-Term",
            "type": "Descriptive",
            "marks": 30.0,
            "schedule": "25 Sep to 1 Oct 2026",
            "start_date": "2026-09-25",
            "end_date": "2026-10-01",
            "covered_lectures": list(range(1, 18)),
            "coverage_assumed": True
        },
        {
            "name": "Continuous Lab Evaluation",
            "type": "Lab",
            "marks": 8.0,
            "schedule": "Respective Labs",
            "start_date": None,
            "end_date": None,
            "covered_lectures": [],
            "coverage_assumed": False
        },
        {
            "name": "Lab Exam",
            "type": "Lab",
            "marks": 4.0,
            "schedule": "Lab 8 or Lab 9",
            "start_date": None,
            "end_date": None,
            "covered_lectures": [],
            "coverage_assumed": False
        },
        {
            "name": "Mini Project",
            "type": "Project",
            "marks": 8.0,
            "schedule": "Lab 5, 10, 12",
            "start_date": None,
            "end_date": None,
            "covered_lectures": [],
            "coverage_assumed": False
        },
        {
            "name": "End-Sem",
            "type": "Descriptive",
            "marks": 50.0,
            "schedule": None,
            "start_date": None,
            "end_date": None,
            "covered_lectures": list(range(1, 37)),
            "coverage_assumed": True
        }
    ]
}

# 3. EOM (HUM 3022)
eom_data = {
    "course_info": {
        "code": "HUM 3022",
        "name": "Essentials of Management",
        "credits": 3,
        "semester": "Odd",
        "academic_year": "2026-2027"
    },
    "outcomes": [
        {"code": "CO1", "statement": "Apply management concepts and understand the importance of social responsibility & ethics in practical aspects of business.", "hours": 8, "marks": 23},
        {"code": "CO2", "statement": "Apply fundamental principles of planning, quality management and strategic decision making for businesses.", "hours": 9, "marks": 22},
        {"code": "CO3", "statement": "Apply fundamental concepts of organizing and delegating authority to manage organizational structures.", "hours": 6, "marks": 19},
        {"code": "CO4", "statement": "Apply systems approach to staffing and human resource management to acquire and retain talent.", "hours": 5, "marks": 17},
        {"code": "CO5", "statement": "Apply principles of leading, communicating and controlling to achieve organizational goals.", "hours": 8, "marks": 19}
    ],
    "lesson_plan": [
        {"lecture_num": 1, "name": "Introduction to Business, Classification of Industries", "co_code": "CO1"},
        {"lecture_num": 2, "name": "Importance of management for an engineer, Manager – Definition & classification, managers and administrators", "co_code": "CO1"},
        {"lecture_num": 3, "name": "Systems Approach to Management, Functions of Managers, 3 Managerial Skills", "co_code": "CO1"},
        {"lecture_num": 4, "name": "14 Principles of Management by Henri Fayol", "co_code": "CO1"},
        {"lecture_num": 5, "name": "14 Principles of Management by Henri Fayol – CONTINUED", "co_code": "CO1"},
        {"lecture_num": 6, "name": "Mintzberg’s 10 roles played by managers", "co_code": "CO1"},
        {"lecture_num": 7, "name": "External Environment, Social Responsibility of managers, Ethics in managing – an integrated approach", "co_code": "CO1"},
        {"lecture_num": 8, "name": "Trust as the Basis for Change Management. International Business", "co_code": "CO1"},
        {"lecture_num": 9, "name": "Types of Plans, Steps in Planning, Objectives, Evolving Concepts in Management by Objectives", "co_code": "CO2"},
        {"lecture_num": 10, "name": "Nature and Purpose of Strategies and Policies", "co_code": "CO2"},
        {"lecture_num": 11, "name": "Quality Management: relevance in management, Total Quality Management (TQM)", "co_code": "CO2"},
        {"lecture_num": 12, "name": "Strategic Quality Planning, SMART quality goals, aligning with MBO", "co_code": "CO2"},
        {"lecture_num": 13, "name": "Strategic Planning Process – Critical Question Analysis", "co_code": "CO2"},
        {"lecture_num": 14, "name": "SWOT & TOWS Matrix: A Modern Tool for Analysis of the Situation", "co_code": "CO2"},
        {"lecture_num": 15, "name": "Blue Ocean Strategy: In Pursuit of Opportunities in Uncontested", "co_code": "CO2"},
        {"lecture_num": 16, "name": "The Portfolio Matrix: A Tool for Allocating Resources", "co_code": "CO2"},
        {"lecture_num": 17, "name": "Porter’s Industry Analysis and Generic Competitive Strategies", "co_code": "CO2"},
        {"lecture_num": 18, "name": "Organizing Process, Span of Management", "co_code": "CO3"},
        {"lecture_num": 19, "name": "Urwick’s Principles of Organizing", "co_code": "CO3"},
        {"lecture_num": 20, "name": "factors affecting the span", "co_code": "CO3"},
        {"lecture_num": 21, "name": "Various methods of Departmentation", "co_code": "CO3"},
        {"lecture_num": 22, "name": "Line and Staff concepts (Line, Staff and Functional Staff authority)", "co_code": "CO3"},
        {"lecture_num": 23, "name": "Delegation- Definition, Principles and Steps", "co_code": "CO3"},
        {"lecture_num": 24, "name": "Difference between HRM and HRD; Job Analysis", "co_code": "CO4"},
        {"lecture_num": 25, "name": "Job Description and Job Specification; Recruitment - methods and sources", "co_code": "CO4"},
        {"lecture_num": 26, "name": "Selection Process, Techniques and Instruments", "co_code": "CO4"},
        {"lecture_num": 27, "name": "Induction and Orientation. Systems Approach to Staffing", "co_code": "CO4"},
        {"lecture_num": 28, "name": "Approaches to Manager Development and Training", "co_code": "CO4"},
        {"lecture_num": 29, "name": "Differences between - Leading and Managing, Leader and Manager", "co_code": "CO5"},
        {"lecture_num": 30, "name": "motives, motivators & motivation. Theories of Motivation - Maslow’s Need Hierarchy", "co_code": "CO5"},
        {"lecture_num": 31, "name": "Herzberg’s Two-Factor Theory and McGregor X and Y. Motivational Techniques", "co_code": "CO5"},
        {"lecture_num": 32, "name": "Leadership Styles - Likert’s Four Systems of Management, Theories, Leadership Grid", "co_code": "CO5"},
        {"lecture_num": 33, "name": "Committees, Teams, and Group Decision-Making", "co_code": "CO5"},
        {"lecture_num": 34, "name": "Communication - Difference between General and Managerial Communication, Types of Communication, Barriers of Communication", "co_code": "CO5"},
        {"lecture_num": 35, "name": "Control Process (steps), Management Control Techniques (Budgetary, Non-budgetary and Network)", "co_code": "CO5"},
        {"lecture_num": 36, "name": "Types of control", "co_code": "CO5"}
    ],
    "sdl_items": [
        {"sl_no": 1, "topic": "Quality Management (SWAYAM)", "hours": 32, "co_code": "CO2"},
        {"sl_no": 2, "topic": "Management Control Techniques (SWAYAM)", "hours": 16, "co_code": "CO5"},
        {"sl_no": 3, "topic": "International Business (SWAYAM)", "hours": 8, "co_code": "CO1"}
    ],
    "sdl_row_hours": [32, 16, 8],
    "sdl_hours_printed_total": 54,
    "sdl_rows_sum": 56,
    "assessments": [
        {
            "name": "Quiz 1",
            "type": "Quiz",
            "marks": 5.0,
            "schedule": "17-29 Aug 2026",
            "start_date": "2026-08-17",
            "end_date": "2026-08-29",
            "covered_lectures": list(range(1, 10)),
            "coverage_assumed": True
        },
        {
            "name": "Mid-Term",
            "type": "Descriptive",
            "marks": 30.0,
            "schedule": None,
            "start_date": None,
            "end_date": None,
            "covered_lectures": list(range(1, 22)),
            "coverage_assumed": True
        },
        {
            "name": "Quiz 2",
            "type": "Quiz",
            "marks": 5.0,
            "schedule": "7-21 Sep 2026",
            "start_date": "2026-09-07",
            "end_date": "2026-09-21",
            "covered_lectures": list(range(18, 29)),
            "coverage_assumed": True
        },
        {
            "name": "Term Project",
            "type": "Project",
            "marks": 10.0,
            "schedule": "Report 4 Oct 2026, presentation from 19 Oct 2026",
            "start_date": "2026-10-04",
            "end_date": "2026-10-19",
            "report_date": "4 Oct 2026",
            "presentation_date": "19 Oct 2026",
            "covered_lectures": list(range(1, 37)),
            "coverage_assumed": True
        },
        {
            "name": "End-Sem",
            "type": "Descriptive",
            "marks": 50.0,
            "schedule": None,
            "start_date": None,
            "end_date": None,
            "covered_lectures": list(range(1, 37)),
            "coverage_assumed": True
        }
    ]
}

# 4. FACD (CSE 3128)
facd_data = {
    "course_info": {
        "code": "CSE 3128",
        "name": "Finite Automata and Compiler Design",
        "credits": 4,
        "semester": "V",
        "academic_year": "2026-2027"
    },
    "outcomes": [
        {"code": "CO1", "statement": "Design grammars and automata for regular languages using the knowledge of grammars, languages, and automata", "hours": 16, "marks": 30},
        {"code": "CO2", "statement": "Identify the steps involved in lexical analyzer generators by familiarizing the different phases of a compiler", "hours": 5, "marks": 12},
        {"code": "CO3", "statement": "Evaluate the top-down and bottom-up parsing techniques by comparing their effectiveness in various computational contexts", "hours": 16, "marks": 33},
        {"code": "CO4", "statement": "Analyze Syntax Directed Translation (SDT) techniques", "hours": 3, "marks": 8},
        {"code": "CO5", "statement": "Analyze expressions to generate appropriate three address code", "hours": 6, "marks": 12},
        {"code": "CO6", "statement": "Apply automated tools such as FLEX and YACC for lexical analysis and parser generation", "hours": 2, "marks": 5}
    ],
    "lesson_plan": [
        {"lecture_num": 1, "name": "Three basic concepts: Languages and It's Operations", "co_code": "CO1"},
        {"lecture_num": 2, "name": "Grammar and Automata", "co_code": "CO1"},
        {"lecture_num": 3, "name": "Deterministic Finite Accepters, Languages and Dfa's, Regular Languages", "co_code": "CO1"},
        {"lecture_num": 4, "name": "Problems on Deterministic Finite Accepter", "co_code": "CO1"},
        {"lecture_num": 5, "name": "Nondeterministic Finite Accepters- Definition of a Nondeterministic Accepter, Why Nondeterminism", "co_code": "CO1"},
        {"lecture_num": 6, "name": "Equivalence of Deterministic and Nondeterministic Finite Accepters", "co_code": "CO1"},
        {"lecture_num": 7, "name": "Reduction of the Number of States in Finite Automata", "co_code": "CO1"},
        {"lecture_num": 8, "name": "Regular Expressions- Formal Definition of a Regular Expression, Languages Associated with Regular Expressions and examples", "co_code": "CO1"},
        {"lecture_num": 9, "name": "Connection between Regular Expressions and Regular Languages, Regular Expressions Denote Regular Languages, Regular Expressions for Regular Languages, Regular Expressions for Describing Simple Patterns", "co_code": "CO1"},
        {"lecture_num": 10, "name": "Regular Grammars-Equivalence of Regular Languages and Regular Grammars", "co_code": "CO1"},
        {"lecture_num": 11, "name": "Identifying Non-regular Languages and Context-Free grammar", "co_code": "CO1"},
        {"lecture_num": 12, "name": "Examples on Context-Free grammar", "co_code": "CO1"},
        {"lecture_num": 13, "name": "Leftmost and Rightmost Derivations, Derivation Trees, Relation Between Sentential Forms and Derivation Trees, Parsing and Ambiguity- Ambiguity in Grammars and Languages", "co_code": "CO1"},
        {"lecture_num": 14, "name": "Nondeterministic Pushdown Automata- Definition of a Pushdown Automaton, The Language Accepted by a Pushdown Automaton", "co_code": "CO1"},
        {"lecture_num": 15, "name": "Examples on Nondeterministic Pushdown Automata", "co_code": "CO1"},
        {"lecture_num": 16, "name": "Examples Pushdown Automata and Context-Free Languages", "co_code": "CO1"},
        {"lecture_num": 17, "name": "Introduction to Language Processors, Structure of Compiler", "co_code": "CO2"},
        {"lecture_num": 18, "name": "The Role of the Lexical Analyzer", "co_code": "CO2"},
        {"lecture_num": 19, "name": "Input Buffering", "co_code": "CO2"},
        {"lecture_num": 20, "name": "Examples on Specifications and Recognition of Tokens", "co_code": "CO2"},
        {"lecture_num": 21, "name": "Problems on Transition-Diagram-Based Lexical Analyzer", "co_code": "CO2"},
        {"lecture_num": 22, "name": "Syntax Analysis - Introduction", "co_code": "CO3"},
        {"lecture_num": 23, "name": "Writing a Grammar- Lexical versus Syntactic Analysis", "co_code": "CO3"},
        {"lecture_num": 24, "name": "Problems on Eliminating Ambiguity and Left Recursion, Left Factoring", "co_code": "CO3"},
        {"lecture_num": 25, "name": "Top-Down Parsing - Recursive-Descent Parsers", "co_code": "CO3"},
        {"lecture_num": 26, "name": "First and Follow(1), LL(1) Grammars", "co_code": "CO3"},
        {"lecture_num": 27, "name": "Non-recursive Predictive Parsing", "co_code": "CO3"},
        {"lecture_num": 28, "name": "Examples on First and Follow(1), LL(1) Grammars, Non-recursive Predictive Parsing", "co_code": "CO3"},
        {"lecture_num": 29, "name": "Bottom-Up Parsing - Reductions, Handle Pruning", "co_code": "CO3"},
        {"lecture_num": 30, "name": "Shift-Reduce Parsing, Introduction to LR parsing- Simple LR, Why LR Parsers?", "co_code": "CO3"},
        {"lecture_num": 31, "name": "Items and LR (0) Automaton, The LR-Parsing Algorithm", "co_code": "CO3"},
        {"lecture_num": 32, "name": "Problems on Constructing SLR-Parsing Tables", "co_code": "CO3"},
        {"lecture_num": 33, "name": "Examples on LR parsing", "co_code": "CO3"},
        {"lecture_num": 34, "name": "More Powerful LR parsers- Canonical LR (1) Items", "co_code": "CO3"},
        {"lecture_num": 35, "name": "Constructing LR(1) Sets of Items, Canonical LR(1) Parsing Tables", "co_code": "CO3"},
        {"lecture_num": 36, "name": "Examples on Canonical LR(1) Parsing Tables", "co_code": "CO3"},
        {"lecture_num": 37, "name": "Conflicts During Shift-Reduce Parsing, Using Ambiguous Grammars-Precedence and Associativity to Resolve Conflicts", "co_code": "CO3"},
        {"lecture_num": 38, "name": "Syntax-Directed Translation - Syntax-Directed Definitions, Evaluation Order for SDD's- Dependency Graphs, Ordering the Evaluation of Attributes", "co_code": "CO4"},
        {"lecture_num": 39, "name": "Applications of Syntax-Directed Translation, Construction of Syntax Trees", "co_code": "CO4"},
        {"lecture_num": 40, "name": "Examples on Syntax-Directed Definitions, Dependency Graphs", "co_code": "CO4"},
        {"lecture_num": 41, "name": "Intermediate-Code Generation - Variants of Syntax Trees, Directed Acyclic Graph for Expressions, The Value Number Method for Constructing DAGs, Three-Address Code, Addresses and Instructions, Quadruples, Triples, Static Single Assignment Form", "co_code": "CO5"},
        {"lecture_num": 42, "name": "Problems on Three Address Code", "co_code": "CO5"},
        {"lecture_num": 43, "name": "Code Generation - Issues in Design of Code Generator", "co_code": "CO5"},
        {"lecture_num": 44, "name": "Examples on Three Address code and Target Language Representation", "co_code": "CO5"},
        {"lecture_num": 45, "name": "Basic Blocks and Flow Graphs and Some Examples", "co_code": "CO5"},
        {"lecture_num": 46, "name": "The DAG Representation of Basic Blocks, Finding Local Common Subexpressions, Dead Code Elimination, Peephole Optimization", "co_code": "CO5"},
        {"lecture_num": 47, "name": "Theory of FLEX- Structure of a FLEX program, Regular Expression, FLEX library functions", "co_code": "CO6"},
        {"lecture_num": 48, "name": "Theory of YACC- YACC Symbols, Symbol values, Symbol Types, YACC Library, Some Example Program", "co_code": "CO6"}
    ],
    "sdl_items": [
        {"sl_no": 1, "topic": "Formal Languages, Finite Automata and Pushdown Automata using NPTEL", "hours": 6, "co_code": "CO1"},
        {"sl_no": 2, "topic": "Automata Design and Language Conversion using JFLAP", "hours": 6, "co_code": "CO1"},
        {"sl_no": 3, "topic": "Building a Lexical Analyzer using Flex", "hours": 6, "co_code": "CO2"},
        {"sl_no": 4, "topic": "Advanced Tokenization and Unicode Support in Modern Compilers", "hours": 6, "co_code": "CO2"},
        {"sl_no": 5, "topic": "Parser Generation using ANTLR", "hours": 6, "co_code": "CO3"},
        {"sl_no": 6, "topic": "Modern Syntax Error Detection and Recovery in Parser Generators", "hours": 6, "co_code": "CO3"},
        {"sl_no": 7, "topic": "Attribute Grammar Systems and Incremental Semantic Analysis", "hours": 6, "co_code": "CO4"},
        {"sl_no": 8, "topic": "Building a Domain-Specific Language (DSL) using ANTLR with Semantic Actions", "hours": 6, "co_code": "CO4"},
        {"sl_no": 9, "topic": "LLVM Intermediate Representation (LLVM IR) and Modern Compiler Optimization", "hours": 6, "co_code": "CO5"},
        {"sl_no": 10, "topic": "Machine-Independent Compiler Optimizations using Static Analysis", "hours": 6, "co_code": "CO5"},
        {"sl_no": 11, "topic": "Case Study – Building a Calculator using Flex and GNU Bison", "hours": 6, "co_code": "CO6"},
        {"sl_no": 12, "topic": "Research Survey – The Deep Learning Compiler: A Comprehensive Survey", "hours": 6, "co_code": "CO6"}
    ],
    "sdl_hours_total": 72,
    "assessments": [
        {
            "name": "Assignment 1",
            "type": "Surprise test",
            "marks": 10.0,
            "covered_lectures": list(range(1, 16)),
            "schedule": "17 Aug 2026 - 29 Aug 2026",
            "start_date": "2026-08-17",
            "end_date": "2026-08-29",
            "coverage_assumed": False
        },
        {
            "name": "Assignment 2",
            "type": "Quiz",
            "marks": 5.0,
            "covered_lectures": list(range(16, 25)),
            "schedule": "7 Sep 2026 - 21 Sep 2026",
            "start_date": "2026-09-07",
            "end_date": "2026-09-21",
            "coverage_assumed": False
        },
        {
            "name": "Mid-Sem",
            "type": "Descriptive",
            "marks": 30.0,
            "covered_lectures": list(range(1, 30)),
            "schedule": "25 Sep 2026 to 1 Oct 2026",
            "start_date": "2026-09-25",
            "end_date": "2026-10-01",
            "coverage_assumed": False
        },
        {
            "name": "Assignment 3",
            "type": "Quiz",
            "marks": 5.0,
            "covered_lectures": list(range(30, 43)),
            "schedule": "19 Oct 2026 - 31 Oct 2026",
            "start_date": "2026-10-19",
            "end_date": "2026-10-31",
            "coverage_assumed": False
        },
        {
            "name": "End-Sem",
            "type": "Descriptive",
            "marks": 50.0,
            "covered_lectures": list(range(1, 49)),
            "schedule": "14 Nov 2026 - 28 Nov 2026",
            "start_date": "2026-11-14",
            "end_date": "2026-11-28",
            "coverage_assumed": False
        }
    ]
}

# Write the 4 files
with open("backend/seed/CSE3148.json", "w", encoding="utf-8") as f:
    json.dump(ml_data, f, indent=2, ensure_ascii=False)

with open("backend/seed/CSE3129.json", "w", encoding="utf-8") as f:
    json.dump(pcap_data, f, indent=2, ensure_ascii=False)

with open("backend/seed/HUM3022.json", "w", encoding="utf-8") as f:
    json.dump(eom_data, f, indent=2, ensure_ascii=False)

with open("backend/seed/CSE3128.json", "w", encoding="utf-8") as f:
    json.dump(facd_data, f, indent=2, ensure_ascii=False)

print("Regenerated all 4 seed JSON files with covered_lectures and coverage_assumed.")
