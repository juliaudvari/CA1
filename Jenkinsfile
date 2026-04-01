pipeline {
    agent any

    environment {
        COMPOSE_PROJECT_NAME = 'jenkins-ca1'
        API_HOST_PORT = '19080'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build and Run Docker') {
            steps {
                powershell '''
                    docker compose down --remove-orphans 2>$null
                    docker-compose down --remove-orphans 2>$null
                    docker compose build --no-cache
                    docker compose up -d
                    $maxAttempts = 30
                    $attempt = 0
                    $apiPort = $env:API_HOST_PORT
                    if (-not $apiPort) { $apiPort = "19080" }
                    while ($attempt -lt $maxAttempts) {
                        try {
                            $r = Invoke-WebRequest -Uri "http://localhost:$apiPort/getAll" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
                            if ($r.StatusCode -eq 200) { break }
                        } catch { }
                        $attempt++
                        Start-Sleep -Seconds 2
                    }
                    Start-Sleep -Seconds 5
                '''
            }
        }

        stage('Run Unit Tests (Newman)') {
            steps {
                powershell '''
                    $npmDir = "$env:APPDATA\\npm"
                    if (-not (Test-Path $npmDir)) { New-Item -ItemType Directory -Path $npmDir -Force | Out-Null }
                    npm install newman
                    $bp = $env:API_HOST_PORT; if (-not $bp) { $bp = "19080" }
                    .\\node_modules\\.bin\\newman run postman_collection.json -e postman_environment.json --env-var "base_url=http://localhost:$bp" --reporters cli
                '''
            }
        }

        stage('Create README') {
            steps {
                powershell '''
                    @"
Inventory Management API - Endpoints Reference
=============================================

Base URL: http://localhost:8000
Interactive API docs: http://localhost:8000/docs

Endpoints:
----------
1. GET  /getSingleProduct?id=<ProductID>
   - Returns single product by ID
   - Param: id (int, required)

2. GET  /getAll
   - Returns all products in JSON format

3. POST /addNew
   - Adds new product (JSON body)
   - Body: {"ProductID": int, "Name": str, "UnitPrice": float, "StockQuantity": int, "Description": str}

4. DELETE /deleteOne?id=<ProductID>
   - Deletes product by ID
   - Param: id (int, required)

5. GET  /startsWith?letter=<char>
   - Returns products whose name starts with letter (e.g. s)
   - Param: letter (single char, required)

6. GET  /paginate?startId=<id>&endId=<id>
   - Returns batch of 10 products between start and end ID
   - Params: startId (int), endId (int), required

7. GET  /convert?id=<ProductID>
   - Returns product price in EUR (converted from USD via live exchange rate)
   - Param: id (int, required)

8. GET  /metrics
   - Prometheus metrics for API monitoring (A-grade)

FastAPI Documentation: http://localhost:8000/docs
"@ | Out-File -FilePath README.txt -Encoding utf8
                '''
            }
        }

        stage('Stop Containers') {
            steps {
                powershell 'docker compose down --remove-orphans 2>$null; docker-compose down --remove-orphans 2>$null'
            }
        }

        stage('Create Zip') {
            steps {
                powershell '''
                    $timestamp = Get-Date -Format "yyyy-MM-dd-HH-mm-ss"
                    $zipName = "complete-$timestamp.zip"
                    $files = @(
                        "main.py", "import_csv_to_mongodb.py", "requirements.txt", "products.csv",
                        "Dockerfile", "docker-compose.yml", "prometheus.yml",
                        "postman_collection.json", "postman_environment.json", "Jenkinsfile", "README.txt"
                    )
                    $existing = $files | Where-Object { Test-Path $_ }
                    Compress-Archive -Path $existing -DestinationPath $zipName -Force
                    Write-Host "Created: $zipName"
                '''
            }
        }
    }

    post {
        always {
            powershell 'docker compose down --remove-orphans 2>$null; docker-compose down --remove-orphans 2>$null'
        }
    }
}
