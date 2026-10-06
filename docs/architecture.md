# Architecture: Cloud Deployment Pipeline (GitHub to AWS ECS Fargate)

## 1. Problem and users
| Deploying a web app by hand is slow and error-prone: someone builds an image, uploads it and clicks through the AWS console, and nobody is sure which version is live. This project automates that path. Every merge to main is tested, packaged into a Docker image and deployed to AWS ECS Fargate without anyone touching the console. The users are the developer (me), visitors to the app, and reviewers or recruiters reading this repo to see how a production-style pipeline is built.

## 2. Requirements

### Functional (what it does)
| ID | Requirement | How we check it |
|---|---|---|
| F1 | GET / returns a JSON welcome message | curl the ALB URL, expect 200 |
| F2 | GET: /health |   return 200 ok to show the app is alive or throw an error | curl <alb:url>/health
| F3 | GET: /version shows the deployed git SHA | curl:github url/version |
| F4 | POST: merge to main deploys automatically | CURL github url |

### Non-functional (how well)
| ID | Requirement | How we check it |
|---|---|---|
| N1 | No long-lived AWS keys anywhere | OIDC role; IAM shows 0 access keys |
| N2 | AWS spend stays under $10/month; hourly resources (ALB, tasks) exist only during a work session| Teardown script runs at the end of each session; the $10 budget sends no alert |
| N3 | A bad deploy can be rolled back to the previous version in under 10 minutes | Redeploy the previous git SHA image; /version shows the old SHA again |
| N4 | Container logs are kept in CloudWatch for 7 days | Logs for a request appear in the CloudWatch log group; retention shows 7 days |
| N5 | Every AWS resource can be deleted and the deletion proven | After teardown, aws ecs list-services, aws elbv2 describe-load-balancers return empty |

## 3. Architecture

 ```mermaid
 (paste the diagram from Lab 3 here)
 ```

### Components
| Component | Job (one line, your words) |
|---|---|
| GitHub repo | Stores the code and history; main is protected so changes only arrive through reviewed PRs |
| GitHub Actions | The robot: on every PR it runs tests; on merge to main it builds the image and deploys it |
| AWS STS + OIDC | Lets GitHub Actions prove who it is to AWS and get temporary credentials, so no AWS keys are stored in GitHub |
| Amazon ECR | AWS's private storage for our Docker images, each tagged with the git commit SHA |
| ECS service (Fargate) | Runs our container and keeps 1 copy alive; Fargate means AWS manages the servers underneath |
| Application Load Balancer | The public front door: takes browser traffic on port 80 and forwards it to a healthy task on port 8000 |
| Security groups | Firewalls: the ALB's allows port 80 from the internet; the task's allows port 8000 only from the ALB's SG |
| CloudWatch Logs | Collects everything the app prints, so we can debug without logging into anything |

| GitHub Actions is a function deploy(commit). OIDC is how it logs in without a hard-coded password. ECR is the storage it writes to. ECS is a while True: loop that keeps the app running. The ALB is the only public entry point.

## 4. Request path
| browser → DNS → ALB:80 → task:8000 → FastAPI
|---|---|---|---|
| Step	| What happens	| Breaks if	| Symptom |
|1	|Browser asks DNS for the ALB's name and gets its IPs	|Wrong name	|DNS error|
|2	|Browser connects to the ALB on port 80 (443 with HTTPS)	|ALB security group doesn't allow it	|Timeout|
|3	|ALB connects to the task's IP on port 8000	|Task SG doesn't allow traffic from the ALB SG|	Timeout|
|4	|Uvicorn, bound to 0.0.0.0:8000, hands the request to FastAPI	|Bound to 127.0.0.1, wrong port, or crashed	|Refused|
|5	|FastAPI returns 200 on /health	|App errors, so the target is unhealthy|	503 from the ALB|



## 5. Key decisions
| Decision | Alternatives considered | Why this one | Trade-off accepted |
|---|---|---|---|
| ALB | NLB; API Gateway; public IP on the task| Understands HTTP, does /health checks, gives a stable DNS name while tasks come and go | $0.0225/h plus public IPs, so it's torn down after each session |
| ECS on Fargate | ECS on EC2; App Runner; Lambda; EKS | No servers to patch; the most common real-world container setup; much simpler than Kubernetes | Slightly higher cost per CPU than EC2; less control |
| No NAT Gateway | Private subnets + NAT; private subnets + VPC endpoints | NAT costs ~$33/month even idle, more than our whole budget | Tasks sit in public subnets with a public IP (for pulling images), protected by the task SG |
| Default VPC (Month 1 only) | Build a custom VPC now | Already exists and is free; this month's focus is the pipeline, not networking | Not production-grade; Month 2 rebuilds it properly with Terraform |
| OIDC instead of access keys | IAM user keys stored as GitHub secrets | Credentials are temporary and scoped to this repo and branch; nothing long-lived can leak | A bit more setup (identity provider + trust policy)|
| Image tag = git SHA | latest; version numbers | Every image traces to an exact commit; rollback = redeploy an old SHA; tags never get overwritten | SHAs are long and not human-friendly |
| Region us-east-1 | af-south-1 (Cape Town); eu-west-1 | Among the cheapest regions, and every service we need is available | Higher latency from Lagos, which doesn't matter for a demo |

## 6. Risks
| Risk | Type | Likelihood | Impact | Mitigation |
| :--- | :--- | :--- | :--- | :--- |
| **A secret or AWS key committed to this public repo** | Security | Medium | High: account takeover, huge bill | OIDC (no keys exist), `.gitignore` for `.env`, stage files by name, GitHub secret scanning |
| **IAM role for GitHub Actions has too many permissions** | Security | Medium | High: a compromised workflow could change anything | Least-privilege policy limited to ECR push and ECS deploy; trust limited to this repo's main |
| **Old images pile up in ECR** | Cost | High | Low (cents) but grows | ECR lifecycle policy keeps only the last 5 images |
| **A deploy breaks `/health` and the site goes down** | Reliability | Medium | Medium: 503 for visitors | Tests in CI before deploy; ECS keeps the old task until the new one is healthy; rollback by SHA |

| How to judge likelihood and impact: ask "how easily could this happen?" and "if it happens, how bad is it?". Use Low / Medium / High. Being honest matters more than being precise.




## 7. Out of scope for Month 1
- HTTPS and a custom domain (needs a domain and certificate; added later)
- Private subnets with VPC endpoints (better security, more cost and setup; Month 2+)
- Terraform (Month 1 is built by hand on purpose so each piece is understood; Month 2 converts it)
- Auto scaling, multiple environments (dev/staging), dashboards and alarms (Months 2-4)
