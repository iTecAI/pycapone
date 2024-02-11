from pycapone import CapOneClient, LoginFlowManager
from dotenv import load_dotenv
from os import environ

load_dotenv()

flow = LoginFlowManager()
result = flow.login_step(
    environ["CO_USER"], environ["CO_PASS"])
valid = flow.execute_mfa(0)
if valid:
    flow.enter_mfa(input("Enter OTP: "))
else:
    exit(0)

flow.wait()
client = CapOneClient.create_from_flow(flow)
