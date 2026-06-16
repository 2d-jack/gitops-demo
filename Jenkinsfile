pipeline {
    agent any

    options {
        ansiColor('xterm')
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    environment {
        REGISTRY      = 'ghcr.io'
        GH_USERNAME   = '2d-jack'
        IMAGE_NAME    = "ghcr.io/2d-jack/gitops-demo"
        SONAR_PROJECT = 'gitops-demo'
    }

    stages {

        // ──────────────────────────────────────────────
        // STAGE 1: Checkout
        // ──────────────────────────────────────────────
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.SHORT_SHA = sh(
                        script: 'git rev-parse --short HEAD',
                        returnStdout: true
                    ).trim()
                    echo "Building commit: ${env.SHORT_SHA}"
                }
            }
        }

        // ──────────────────────────────────────────────
        // STAGE 2: Secret Detection
        // Scans ALL git history for leaked secrets.
        // Fails immediately if any secret is found.
        // ──────────────────────────────────────────────
        stage('Secret Scan — Gitleaks') {
            steps {
                echo '🔍 Scanning for hardcoded secrets...'
                sh '''
                    gitleaks detect \
                        --source . \
                        --verbose \
                        --report-format json \
                        --report-path gitleaks-report.json \
                        --exit-code 1 \
                        || (echo "❌ SECRETS FOUND IN CODE — pipeline stopped" && exit 1)
                '''
                echo '✅ No secrets found'
            }
            post {
                always {
                    archiveArtifacts artifacts: 'gitleaks-report.json',
                                     allowEmptyArchive: true
                }
            }
        }

        // ──────────────────────────────────────────────
        // STAGE 3: Dependency Scan (SCA)
        // Scans requirements.txt for packages with
        // known CVEs from the OSV/PyPI advisory database.
        // ──────────────────────────────────────────────
        stage('Dependency Scan — pip-audit') {
            steps {
                echo '📦 Scanning Python dependencies for CVEs...'
                sh '''
                    pip-audit \
                        -r app/requirements.txt \
                        --format columns \
                        --output pip-audit-report.json \
                        --format json \
                        || true

                    pip-audit \
                        -r app/requirements.txt \
                        --format columns
                '''
                echo '✅ Dependency scan complete'
            }
            post {
                always {
                    archiveArtifacts artifacts: 'pip-audit-report.json',
                                     allowEmptyArchive: true
                }
            }
        }

        // ──────────────────────────────────────────────
        // STAGE 4: Unit Tests + Coverage
        // Runs pytest and generates coverage.xml
        // which SonarQube will read in the next stage.
        // ──────────────────────────────────────────────
        stage('Unit Tests + Coverage') {
            steps {
                echo '🧪 Running tests with coverage...'
                sh '''
                    pip3 install -r app/requirements.txt pytest pytest-cov --break-system-packages --quiet

                    cd app
                    python3 -m pytest tests/ \
                        -v \
                        --tb=short \
                        --cov=. \
                        --cov-report=xml:../coverage.xml \
                        --cov-report=html:../coverage-html \
                        --cov-report=term-missing
                '''
            }
            post {
                always {
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'coverage-html',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report'
                    ])
                }
            }
        }

        // ──────────────────────────────────────────────
        // STAGE 5: SonarQube Analysis
        // SAST: Detects security bugs, code smells,
        // vulnerabilities, and security hotspots
        // in your Python source code.
        // ──────────────────────────────────────────────
        stage('SonarQube Analysis') {
            steps {
                echo '🔒 Running SAST and code quality analysis...'
                withSonarQubeEnv('SonarQube') {
                    sh '''
                        sonar-scanner \
                            -Dsonar.projectKey=${SONAR_PROJECT} \
                            -Dsonar.projectVersion=${SHORT_SHA} \
                            -Dsonar.sources=app \
                            -Dsonar.tests=app/tests \
                            -Dsonar.exclusions=app/tests/** \
                            -Dsonar.python.version=3.12 \
                            -Dsonar.python.coverage.reportPaths=coverage.xml \
                            -Dsonar.sourceEncoding=UTF-8
                    '''
                }
                echo '✅ SonarQube analysis submitted'
            }
        }

        // ──────────────────────────────────────────────
        // STAGE 6: Quality Gate
        // Waits for SonarQube to finish analysis and
        // checks the result. If Quality Gate FAILS
        // (security rating < A, hotspots not reviewed,
        // etc.) the entire pipeline is aborted.
        // ──────────────────────────────────────────────
        stage('Quality Gate') {
            steps {
                echo '🚦 Waiting for Quality Gate result...'
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
                echo '✅ Quality Gate passed'
            }
        }

        // ──────────────────────────────────────────────
        // STAGE 7: IaC Security Scan
        // Scans your Kubernetes YAML files for
        // misconfigurations (no resource limits,
        // running as root, privileged containers, etc.)
        // ──────────────────────────────────────────────
        stage('IaC Scan — Trivy Config') {
            steps {
                echo '🏗️ Scanning Kubernetes manifests for misconfigurations...'
                sh '''
                    trivy config k8s/ \
                        --severity HIGH,CRITICAL \
                        --format table \
                        --exit-code 0

                    echo "--- Failing on CRITICAL misconfigurations ---"
                    trivy config k8s/ \
                        --severity CRITICAL \
                        --format table \
                        --exit-code 1
                '''
                echo '✅ IaC scan passed'
            }
        }

        // ──────────────────────────────────────────────
        // STAGE 8: Docker Build
        // ──────────────────────────────────────────────
        stage('Docker Build') {
            steps {
                echo "🐳 Building Docker image: ${IMAGE_NAME}:${SHORT_SHA}"
                sh """
                    docker build \
                        -t ${IMAGE_NAME}:${env.SHORT_SHA} \
                        -t ${IMAGE_NAME}:latest \
                        ./app
                """
                echo '✅ Docker image built'
            }
        }

        // ──────────────────────────────────────────────
        // STAGE 9: Container Image Scan
        // Scans the built image for OS and library
        // vulnerabilities BEFORE it is pushed to the
        // registry. Image is NOT pushed if CRITICAL
        // vulnerabilities with available fixes are found.
        // ──────────────────────────────────────────────
        stage('Container Scan — Trivy Image') {
            steps {
                echo '🐳 Scanning container image for vulnerabilities...'
                sh """
                    trivy image \
                        --severity HIGH,CRITICAL \
                        --ignore-unfixed \
                        --format table \
                        --exit-code 0 \
                        ${IMAGE_NAME}:${env.SHORT_SHA}

                    echo "--- Failing on unfixed CRITICAL CVEs ---"
                    trivy image \
                        --severity CRITICAL \
                        --ignore-unfixed \
                        --format table \
                        --exit-code 1 \
                        ${IMAGE_NAME}:${env.SHORT_SHA}
                """
                echo '✅ Container scan passed — no critical CVEs'
            }
        }

        // ──────────────────────────────────────────────
        // STAGE 10: Push to GHCR
        // Only reached if ALL security gates above pass.
        // ──────────────────────────────────────────────
        stage('Push to GHCR') {
            steps {
                echo "📤 Pushing image to ghcr.io..."
                withCredentials([string(credentialsId: 'github-pat', variable: 'GH_PAT')]) {
                    sh """
                        echo "${GH_PAT}" | docker login ghcr.io \
                            -u ${GH_USERNAME} \
                            --password-stdin

                        docker push ${IMAGE_NAME}:${env.SHORT_SHA}
                        docker push ${IMAGE_NAME}:latest
                    """
                }
                echo "✅ Pushed: ${IMAGE_NAME}:${env.SHORT_SHA}"
            }
        }

        // ──────────────────────────────────────────────
        // STAGE 11: Update GitOps Manifest
        // Updates k8s/deployment.yaml with the new
        // image tag and commits it to GitHub.
        // ArgoCD detects this change and deploys.
        // ──────────────────────────────────────────────
        stage('Update GitOps Manifest') {
            steps {
                echo '📝 Updating Kubernetes manifest with new image tag...'
                withCredentials([string(credentialsId: 'github-pat', variable: 'GH_PAT')]) {
                    sh """
                        git config user.name "jenkins-bot"
                        git config user.email "jenkins@ci.local"

                        # Update image tag
                        sed -i "s|image: ${IMAGE_NAME}:.*|image: ${IMAGE_NAME}:${env.SHORT_SHA}|g" k8s/deployment.yaml

                        # Update APP_VERSION to git SHA
                        sed -i 's|value: "[0-9a-f]*"  # APP_VERSION|value: "${env.SHORT_SHA}"  # APP_VERSION|g' k8s/deployment.yaml

                        echo "Updated manifest:"
                        grep -E "image:|APP_VERSION" k8s/deployment.yaml -A1

                        git add k8s/deployment.yaml
                        git commit -m "ci: deploy ${env.SHORT_SHA} — all security gates passed [skip ci]"

                        git push https://${GH_USERNAME}:${GH_PAT}@github.com/${GH_USERNAME}/gitops-demo.git HEAD:main
                    """
                }
                echo '✅ Manifest updated — ArgoCD will now sync'
            }
        }
    }

    post {
        success {
            echo """
            ╔══════════════════════════════════════╗
            ║  ✅ PIPELINE SUCCEEDED               ║
            ║                                      ║
            ║  Security Gates:                     ║
            ║  ✅ Gitleaks (no secrets)            ║
            ║  ✅ pip-audit (no CVE deps)          ║
            ║  ✅ SonarQube (quality gate)         ║
            ║  ✅ Trivy config (K8s manifests)     ║
            ║  ✅ Trivy image (container)          ║
            ║                                      ║
            ║  Deployed: ${env.SHORT_SHA}
            ╚══════════════════════════════════════╝
            """
        }
        failure {
            echo """
            ╔══════════════════════════════════════╗
            ║  ❌ PIPELINE FAILED                  ║
            ║  Check the stage that failed above   ║
            ╚══════════════════════════════════════╝
            """
        }
        always {
            sh 'docker rmi ${IMAGE_NAME}:${SHORT_SHA} --force || true'
            cleanWs()
        }
    }
}
