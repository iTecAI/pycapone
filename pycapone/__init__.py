import time
from httpx import Client
import user_agent
from selenium import webdriver
from selenium.webdriver.common.by import By


class LoginFlowManager:
    def __init__(self):
        self.cookies = None
        self.agent = None
        options = webdriver.ChromeOptions()
        options.add_argument("--devtools")
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': """
            Object.defineProperty(Navigator.prototype, 'webdriver', {
                set: undefined,
                enumerable: true,
                configurable: true,
                get: new Proxy(
                    Object.getOwnPropertyDescriptor(Navigator.prototype, 'webdriver').get,
                    { apply: (target, thisArg, args) => {
                        // emulate getter call validation
                        Reflect.apply(target, thisArg, args);
                        return false;
                    }}
                )
            });
        """})
        self.driver.implicitly_wait(2)

    def login_step(self, username: str, password: str) -> None | list[str]:
        self.driver.get("https://verified.capitalone.com/auth/signin")
        userInput = self.driver.find_element(value="usernameInputField")
        passwordInput = self.driver.find_element(value="pwInputField")
        submitButton = self.driver.find_element(
            by=By.CSS_SELECTOR, value="html body.ci-root identity-experience-auth-root main.main-body.content identity-experience-auth-sign-in codex-content-card div.content-card.content-card--small div.content-card-inner--narrow ent-sign-in-form form.ng-untouched.ng-pristine.ng-invalid div.ci-margin-bottom-medium.ci-margin-top-xlarge button.c1-ease-button--full-width.c1-ease-button.c1-ease-button--action")
        userInput.send_keys(username)
        passwordInput.send_keys(password)
        submitButton.click()
        time.sleep(2)
        if self.driver.current_url.startswith("https://verified.capitalone.com/step-up/"):
            self.mfa_options = self.driver.find_elements(by=By.CSS_SELECTOR,
                                                         value="body > identity-experience-step-up-root > div > div > step-up > div > mfa-options-display > codex-option-list > div > div > codex-option-list-entry")
            return [i.text for i in self.mfa_options]
        else:
            self.mfa_options = None
            return None

    def execute_mfa(self, index: int) -> bool:
        if not self.mfa_options:
            return
        self.mfa_options[index].click()
        time.sleep(2)
        submit_btns = self.driver.find_elements(
            by=By.CSS_SELECTOR, value="button[type=submit]")
        if len(submit_btns) > 0:
            submit_btns[0].click()
            return True
        return False

    def enter_mfa(self, data: str) -> bool:
        self.driver.find_element(value="pinEntry").send_keys(data)
        self.driver.find_element(
            by=By.CSS_SELECTOR, value="button[type=submit]").click()

    def wait(self):
        while not self.driver.current_url.endswith("accountSummary"):
            time.sleep(0.5)

        self.cookies = {c["name"]: c["value"]
                        for c in self.driver.get_cookies()}
        self.agent = self.driver.execute_script(
            "return window.navigator.userAgent")
        self.driver.close()


class CapOneClient:
    def __init__(self, agent: str = None, authentication_context: dict[str, str] = {}):
        self.user_agent = agent if agent else user_agent.generate_user_agent(
            navigator=("chrome",), device_type=("desktop",))

        self.client = Client(headers={
            "User-Agent": self.user_agent
        }, cookies=authentication_context)

        print(self.client.get("https://myaccounts.capitalone.com/accountSummary",
              headers={"Host": "myaccounts.capitalone.com"}))

    @classmethod
    def create_from_flow(cls, flow: LoginFlowManager) -> "CapOneClient":
        return CapOneClient(agent=flow.agent, authentication_context=flow.cookies)
