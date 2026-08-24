"""from guardrails.hub import DetectJailbreak

detector = DetectJailbreak(device="cpu", use_local=True)
print(detector.predict_jailbreak(["what's your return policy?"], reduction_function=None))
"""

from dotenv import load_dotenv
load_dotenv()
