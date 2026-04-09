# Architecture Specification: VC-LMS (Version Control Learning Management System)

## 1. High-Level Design (HLD)

### 1.1 Architectural Overview
The VC-LMS is built on a **Decoupled Microservices Architecture** with a focus on **State-Persistent Versioning**. Unlike traditional CRUD-based systems, VC-LMS utilizes an event-driven approach to handle file mutations, treating every change as an immutable record within a Directed Acyclic Graph (DAG).

### 1.2 Core System Components
- **API Gateway (Orchestration Layer):** Validates incoming requests and routes traffic to the Versioning Engine or Metadata Service.
- **State-Persistent Versioning Engine:** The core logic handler for "commits," hashing, and state transitions.
- **Content-Addressable Storage (CAS):** An immutable blob storage system where file names are derived from their cryptographic content (SHA-256).
- **Metadata Orchestrator (DAG Management):** A relational database (PostgreSQL) that tracks the lineage, parent-child relationships, and pointers to the CAS.
- **CI/CD Integration Bridge:** A webhook-based service that triggers automated testing/linting upon each "commit" (upload).

## 2. Low-Level Design (LLD)

### 2.1 Module: State-Persistent Versioning Engine
This module is responsible for the transition from "File Upload" to "Versioned Asset."
- **Logic:** 1. Receive raw binary stream.
  2. Compute **SHA-256 Checksum**.
  3. Query Metadata Orchestrator to check for hash collision (de-duplication).
  4. If unique, initiate write to CAS and generate a new Version ID.

### 2.2 Module: Immutable Storage Architecture
- **Implementation:** Utilizes an S3-compliant object store (e.g., MinIO/AWS S3) with "Versioning" and "Object Lock" enabled.
- **Pathing Logic:** Files are stored in a tiered directory structure based on the hash (e.g., `/af/2c/af2c30...`) to prevent filesystem performance degradation.

### 2.3 Module: Delta-Encoding Service
- **Function:** To minimize storage footprint for text-heavy academic submissions.
- **Mechanism:** When a user uploads "Version N+1," the service calculates the binary diff (using VCDIFF or similar algorithms) against "Version N" and stores only the delta.

### 2.4 Module: Atomic Transaction Handler
- **Purpose:** Ensures data integrity during multi-file commits (e.g., a project folder).
- **Workflow:** Implements Two-Phase Commit (2PC). Metadata is not updated until the binary write to CAS is confirmed by an ACK signal.

## 3. System Workflow

### 3.1 Submission & Commit Workflow
1. **Initiate:** User pushes a file/directory via the Frontend/CLI.
2. **Preprocessing:** The API Gateway intercepts the stream and calculates the cryptographic signature.
3. **Collision Check:** The system verifies if the content already exists in the global CAS pool (De-duplication).
4. **DAG Update:** A new node is added to the student's submission tree. The "HEAD" pointer moves to the new Version ID.
5. **Persistence:** The binary is committed to storage, and a "Success" receipt is returned with the GPG-signed commit hash.

### 3.2 Retrieval & Reconstruction Workflow
1. **Request:** User requests "Assignment_Draft_v2."
2. **Lookup:** The Metadata Orchestrator finds the Version ID and its associated CAS pointer.
3. **Reassembly:** If the file is stored as a delta, the Delta-Encoding Service fetches the base version and applies the diffs sequentially.
4. **Delivery:** The reconstructed file is streamed to the user.

## 4. Technical Stack & Specifications
- **Core Engine:** Python 3.12 / FastAPI.
- **Data Persistence:** PostgreSQL (Metadata) + MinIO (Blobs).
- **Security:** SHA-256 for integrity; JWT + OAuth2 for identity; GPG for commit signing.
- **Concurrency:** Redis-backed task queue (Celery) for asynchronous delta calculations.

## 5. Security & Auditability
- **Immutable Audit Log:** Every interaction is recorded in a non-volatile ledger.
- **Forensic Visibility:** Instructors can view the "diff" between any two points in time to monitor the progress of student work.
