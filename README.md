# gitops-demo

graph TD
    %% Color definitions and styles
    classDef dev fill:#ffe6cc,stroke:#d79b00,stroke-width:2px,color:#000;
    classDef github fill:#dae8fc,stroke:#6c8ebf,stroke-width:2px,color:#000;
    classDef server fill:#f5f5f5,stroke:#666,stroke-width:2px,color:#000,stroke-dasharray: 5 5;
    classDef jenkins fill:#d5e8d4,stroke:#82b366,stroke-width:2px,color:#000;
    classDef stage fill:#fff2cc,stroke:#d6b656,stroke-width:2px,color:#000;
    classDef sonar fill:#e1d5e7,stroke:#9673a6,stroke-width:2px,color:#000;
    classDef k3s fill:#f8cecc,stroke:#b85450,stroke-width:2px,color:#000;
    classDef registry fill:#e51400,stroke:#b10000,stroke-width:2px,color:#fff;

    Developer[Developer]:::dev
    Repo[GitHub Repository<br>source code + k8s manifests]:::github
    Registry[ghcr.io<br>Container Registry]:::registry

    subgraph Ubuntu_Server [Ubuntu Server]
        direction TB
        
        subgraph Jenkins_Service [Jenkins :8080]
            direction TB
            S1[Stage 1: Checkout]:::stage
            S2[Stage 2: Secret Scan<br>Gitleaks]:::stage
            S3[Stage 3: Dependency Scan<br>pip-audit]:::stage
            S4[Stage 4: Unit Tests + Coverage<br>pytest]:::stage
            S5[Stage 5: SonarQube Analysis<br>sonar-scanner]:::stage
            S6[Stage 6: Quality Gate<br>Pass/Fail]:::stage
            S7[Stage 7: IaC Scan<br>Trivy Config]:::stage
            S8[Stage 8: Docker Build]:::stage
            S9[Stage 9: Container Scan<br>Trivy Image]:::stage
            S10[Stage 10: Push to GHCR]:::stage
            S11[Stage 11: Update GitOps Manifest]:::stage
            
            S1 --> S2 --> S3 --> S4 --> S5 --> S6 --> S7 --> S8 --> S9 --> S10 --> S11
        end

        Sonar[SonarQube :9000<br>- SAST Analysis<br>- Code Quality<br>- Test Coverage<br>- Security Hotspots]:::sonar
        
        subgraph K3s_Cluster [K3s Cluster]
            Argo[ArgoCD<br>GitOps Controller]:::k3s
            App[gitops-app<br>Flask Pods]:::k3s
            Argo -->|Deploys / Syncs| App
        end
    end

    %% Pipeline interactions
    Developer -->|git push| Repo
    Repo -->|Polls every 1 min| S1
    S5 -->|Sends data| Sonar
    Sonar -->|Webhook notification| S6
    S10 -->|Pushes built image| Registry
    S11 -->|Pushes manifest update| Repo
    Repo -->|Git sync| Argo
    App -->|Pulls deployment image| Registry

    %% Assign styles to blocks
    style Ubuntu_Server fill:#fafafa,stroke:#333,stroke-width:2px
    style Jenkins_Service fill:#eff7ed,stroke:#82b366,stroke-width:1px
    style K3s_Cluster fill:#fff0f0,stroke:#b85450,stroke-width:1px
