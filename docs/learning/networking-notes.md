What's an IP?
IP stands for internet protocol. The is the address of a machine or computer that will allow other computer to communicate with it. 
This can be liken to the name of a Resturant, of which without, you can't locate the resturant.
Port: This is the location of a particular service inside the resturant
DNS: This is the address of the resturant again but in a more readable format or easy for human eyes to understand.

Refused vs timeout, and what each tells you to check.
Refuse the request was rejected. This tells us that the required endpoint is not available or does not exist though the request got to the machine.

Why the container must bind to 0.0.0.0
So the application listen on the container network interface and not inside the container and can receive traffic from anywhere

Browser → DNS → ALB → Fargate → FastAPI.

The browser asks DNS for the ALB's name and gets back the ALB's IPs. It connects to the ALB on port 80 (the ALB's SG must allow it). The ALB forwards the request to the Fargate task's IP on port 8000 (the task's SG must allow the ALB). Uvicorn, bound to 0.0.0.0, hands the request to FastAPI, which returns 200 on /health.
