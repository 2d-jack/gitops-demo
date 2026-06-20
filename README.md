# gitops-demo

flowchart TB

    Dev[Developer]
    GH[GitHub Repository<br/>Source Code + K8s Manifests]
    REG[ghcr.io Registry]

    Dev -->|git push| GH

    subgraph Ubuntu["Ubuntu Server"]
        direction TB

        JENKINS[Jenkins :8080<br/><br/>
        Stage 1 - Gitleaks (Secret Detection)<br/>
        Stage 2 - pip-audit (Dependency CVE Scan)<br/>
        Stage 3 - Tests + Coverage<br/>
        Stage 4 - SonarQube (SAST + Quality + Hotspots)<br/>
        Stage 5 - Quality Gate (Pass/Fail)<br/>
        Stage 6 - Trivy Config (K8s Manifest Scan)<br/>
        Stage 7 - Docker Build<br/>
        Stage 8 - Trivy Image (Container CVE Scan)<br/>
        Stage 9 - Push GHCR<br/>
        Stage 10 - Update GitOps Manifest]

        SONAR[SonarQube :9000<br/>- SAST<br/>- Code Quality<br/>- Coverage<br/>- Hotspots]

        subgraph K3S["K3s Cluster"]
            direction TB
            ARGO[ArgoCD (GitOps)]
            APP[gitops-app (Flask)]
            ARGO --> APP
        end

        JENKINS --> SONAR
    end

    GH -->|Poll every 10 min| JENKINS
    JENKINS -->|Push Image| REG
    JENKINS -->|Update Manifest| GH
    GH -->|Sync GitOps Changes| ARGO
