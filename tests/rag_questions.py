"""Labeled questions for retrieval evaluation (Phase 3).

`expected` lists the doc ids that contain the answer; retrieving a chunk from ANY
of them counts as a hit (several docs often answer the same question, e.g. the
FAQ and the policy it summarizes). An empty list means the KB has no answer.

kinds:
  product       a fact from one product file
  near-dup      a product with look-alike neighbors (t-shirts, earbuds, mugs, chocolate)
  exact-term    a bare spec or model term, which dense embeddings handle poorly
  policy        a policy / FAQ question, phrased the way a customer would
  cross-lingual German (de) or Chinese (zh) question over the English KB
  no-answer     nothing in the KB answers it (off-topic, or a product we don't sell)
"""

QUESTIONS = [
    # --- products -------------------------------------------------------------
    {"id": "p-01", "kind": "product", "lang": "en", "query": "What sizes does the basic t-shirt come in?", "expected": ["prod-001"]},
    {"id": "p-02", "kind": "near-dup", "lang": "en", "query": "How long does the battery last on the noise-cancelling earbuds?", "expected": ["prod-002"]},
    {"id": "p-03", "kind": "near-dup", "lang": "en", "query": "Which earbuds won't fall out while I'm running?", "expected": ["prod-013"]},
    {"id": "p-04", "kind": "near-dup", "lang": "en", "query": "Do the over-ear headphones have noise cancellation?", "expected": ["prod-014"]},
    {"id": "p-05", "kind": "product", "lang": "en", "query": "Can I take the power bank on a plane?", "expected": ["prod-016"]},
    {"id": "p-06", "kind": "product", "lang": "en", "query": "Can I go swimming with the smartwatch?", "expected": ["prod-018"]},
    {"id": "p-07", "kind": "near-dup", "lang": "en", "query": "Can I put the travel mug in the dishwasher?", "expected": ["prod-021"]},
    {"id": "p-08", "kind": "near-dup", "lang": "en", "query": "Is the 12oz ceramic coffee mug dishwasher safe?", "expected": ["prod-003"]},
    {"id": "p-09", "kind": "near-dup", "lang": "en", "query": "Are the dark chocolate bars vegan?", "expected": ["prod-029"]},
    {"id": "p-10", "kind": "near-dup", "lang": "en", "query": "Does the chocolate gift box contain nuts?", "expected": ["prod-004"]},
    {"id": "p-11", "kind": "product", "lang": "en", "query": "When will the holiday gift basket be available again?", "expected": ["prod-034"]},
    {"id": "p-12", "kind": "product", "lang": "en", "query": "Do digital gift cards expire?", "expected": ["prod-033"]},
    {"id": "p-13", "kind": "product", "lang": "en", "query": "Will my 15 inch laptop fit in the backpack?", "expected": ["prod-037"]},
    {"id": "p-14", "kind": "near-dup", "lang": "en", "query": "Is the V-neck cut slimmer than the regular tee?", "expected": ["prod-005"]},
    {"id": "p-15", "kind": "near-dup", "lang": "en", "query": "I need a warm shirt with long sleeves for autumn", "expected": ["prod-006"]},
    {"id": "p-16", "kind": "product", "lang": "en", "query": "How many watts does the USB-C cable support?", "expected": ["prod-017"]},
    {"id": "p-17", "kind": "product", "lang": "en", "query": "Can I charge my earbuds on the wireless charging pad?", "expected": ["prod-020"]},
    {"id": "p-18", "kind": "product", "lang": "en", "query": "Do you sell a yoga mat?", "expected": ["prod-040"]},
    {"id": "p-19", "kind": "product", "lang": "en", "query": "How much is the French press?", "expected": ["prod-023"]},
    {"id": "p-20", "kind": "product", "lang": "en", "query": "Is the honey safe for my 6 month old baby?", "expected": ["prod-032"]},
    {"id": "p-21", "kind": "product", "lang": "en", "query": "Do you have loose leaf tea?", "expected": ["prod-031"]},
    {"id": "p-22", "kind": "product", "lang": "en", "query": "I want a speaker I can take to the beach", "expected": ["prod-015"]},
    {"id": "p-23", "kind": "exact-term", "lang": "en", "query": "10000mAh", "expected": ["prod-016"]},
    {"id": "p-24", "kind": "exact-term", "lang": "en", "query": "IPX5", "expected": ["prod-013"]},
    {"id": "p-25", "kind": "exact-term", "lang": "en", "query": "UV400", "expected": ["prod-038"]},

    # --- policies & FAQ -------------------------------------------------------
    {"id": "q-01", "kind": "policy", "lang": "en", "query": "I wore the shirt once, can I still return it?", "expected": ["faq-general", "pol-returns"]},
    {"id": "q-02", "kind": "policy", "lang": "en", "query": "Do you charge a restocking fee?", "expected": ["faq-general", "pol-returns"]},
    {"id": "q-03", "kind": "policy", "lang": "en", "query": "Who pays for the return shipping?", "expected": ["pol-returns"]},
    {"id": "q-04", "kind": "policy", "lang": "en", "query": "When do I get my money back after sending something back?", "expected": ["faq-general", "pol-refunds"]},
    {"id": "q-05", "kind": "policy", "lang": "en", "query": "Can my refund go to a different card?", "expected": ["faq-general", "pol-refunds", "pol-payment"]},
    {"id": "q-06", "kind": "policy", "lang": "en", "query": "Can I swap my hoodie for a bigger size?", "expected": ["faq-general", "pol-exchanges"]},
    {"id": "q-07", "kind": "policy", "lang": "en", "query": "My mug arrived broken", "expected": ["pol-damaged"]},
    {"id": "q-08", "kind": "policy", "lang": "en", "query": "The chocolates arrived melted", "expected": ["pol-damaged"]},
    {"id": "q-09", "kind": "policy", "lang": "en", "query": "My earbuds stopped charging after four months", "expected": ["pol-warranty", "pol-damaged"]},
    {"id": "q-10", "kind": "policy", "lang": "en", "query": "Can I use two promo codes on one order?", "expected": ["faq-general", "pol-discounts"]},
    {"id": "q-11", "kind": "policy", "lang": "en", "query": "Does my loyalty discount stack with a promo code?", "expected": ["pol-discounts", "pol-loyalty"]},
    {"id": "q-12", "kind": "policy", "lang": "en", "query": "How do I join the loyalty program?", "expected": ["pol-loyalty"]},
    {"id": "q-13", "kind": "policy", "lang": "en", "query": "I want to cancel my order", "expected": ["pol-order-changes"]},
    {"id": "q-14", "kind": "policy", "lang": "en", "query": "I forgot to enter my promo code before paying", "expected": ["pol-order-changes", "pol-discounts"]},
    {"id": "q-15", "kind": "policy", "lang": "en", "query": "Tracking says delivered but there's no package", "expected": ["pol-order-tracking"]},
    {"id": "q-16", "kind": "policy", "lang": "en", "query": "Do you accept PayPal?", "expected": ["pol-payment"]},
    {"id": "q-17", "kind": "policy", "lang": "en", "query": "Can I pay part with a gift card and the rest by credit card?", "expected": ["pol-payment", "prod-033"]},
    {"id": "q-18", "kind": "policy", "lang": "en", "query": "How fast is expedited shipping?", "expected": ["faq-general", "pol-shipping-domestic"]},
    {"id": "q-19", "kind": "policy", "lang": "en", "query": "How much do I have to spend to get free shipping?", "expected": ["faq-general", "pol-shipping-domestic"]},
    {"id": "q-20", "kind": "policy", "lang": "en", "query": "Who pays customs duties on international orders?", "expected": ["faq-general", "pol-shipping-international"]},
    {"id": "q-21", "kind": "policy", "lang": "en", "query": "Can I send a present directly to my friend?", "expected": ["pol-gift-orders"]},
    {"id": "q-22", "kind": "policy", "lang": "en", "query": "Someone gave me a gift, can I return it?", "expected": ["pol-gift-orders"]},
    {"id": "q-23", "kind": "policy", "lang": "en", "query": "Please reset my password", "expected": ["faq-general", "pol-account-security"]},
    {"id": "q-24", "kind": "policy", "lang": "en", "query": "My account got locked after too many tries", "expected": ["faq-general", "pol-account-security"]},
    {"id": "q-25", "kind": "policy", "lang": "en", "query": "How do I delete my account?", "expected": ["pol-account-management"]},
    {"id": "q-26", "kind": "policy", "lang": "en", "query": "Can I order without creating an account?", "expected": ["pol-account-management"]},
    {"id": "q-27", "kind": "policy", "lang": "en", "query": "What is your company's bank account number?", "expected": ["pol-privacy"]},
    {"id": "q-28", "kind": "policy", "lang": "en", "query": "Am I chatting with a real person?", "expected": ["faq-general"]},
    {"id": "q-29", "kind": "policy", "lang": "en", "query": "How can I reach a human agent?", "expected": ["faq-general", "pol-contact"]},
    {"id": "q-30", "kind": "policy", "lang": "en", "query": "Does the warranty cover water damage?", "expected": ["pol-warranty"]},

    # --- cross-lingual --------------------------------------------------------
    {"id": "x-01", "kind": "cross-lingual", "lang": "de", "query": "Kann ich getragene Kleidung zurückgeben?", "expected": ["faq-general", "pol-returns"]},
    {"id": "x-02", "kind": "cross-lingual", "lang": "de", "query": "Wie lange dauert die Rückerstattung?", "expected": ["faq-general", "pol-refunds"]},
    {"id": "x-03", "kind": "cross-lingual", "lang": "de", "query": "Liefert ihr nach Deutschland und was kostet das?", "expected": ["faq-general", "pol-shipping-international"]},
    {"id": "x-04", "kind": "cross-lingual", "lang": "de", "query": "Ich habe mein Passwort vergessen", "expected": ["faq-general", "pol-account-security"]},
    {"id": "x-05", "kind": "cross-lingual", "lang": "de", "query": "Hat die Smartwatch GPS?", "expected": ["prod-018"]},
    {"id": "x-06", "kind": "cross-lingual", "lang": "de", "query": "Meine Bestellung ist beschädigt angekommen", "expected": ["pol-damaged"]},
    {"id": "x-07", "kind": "cross-lingual", "lang": "zh", "query": "退货期限是多久？", "expected": ["faq-general", "pol-returns"]},
    {"id": "x-08", "kind": "cross-lingual", "lang": "zh", "query": "可以同时使用两个优惠码吗？", "expected": ["faq-general", "pol-discounts"]},
    {"id": "x-09", "kind": "cross-lingual", "lang": "zh", "query": "运动耳机防水吗？", "expected": ["prod-013"]},
    {"id": "x-10", "kind": "cross-lingual", "lang": "zh", "query": "国际运费是多少？", "expected": ["faq-general", "pol-shipping-international"]},
    {"id": "x-11", "kind": "cross-lingual", "lang": "zh", "query": "我想取消订单", "expected": ["pol-order-changes"]},
    {"id": "x-12", "kind": "cross-lingual", "lang": "zh", "query": "礼品卡会过期吗？", "expected": ["prod-033"]},

    # --- no answer in the KB --------------------------------------------------
    {"id": "n-01", "kind": "no-answer", "lang": "en", "query": "What's the weather in Berlin tomorrow?", "expected": []},
    {"id": "n-02", "kind": "no-answer", "lang": "en", "query": "Do you sell laptops?", "expected": []},
    {"id": "n-03", "kind": "no-answer", "lang": "en", "query": "Do you have a physical store in Paris?", "expected": []},
    {"id": "n-04", "kind": "no-answer", "lang": "en", "query": "Write me a poem about the ocean", "expected": []},
    {"id": "n-05", "kind": "no-answer", "lang": "en", "query": "Do you sell dog food?", "expected": []},
    {"id": "n-06", "kind": "no-answer", "lang": "en", "query": "Can you recommend a good movie?", "expected": []},
    {"id": "n-07", "kind": "no-answer", "lang": "de", "query": "Wie wird das Wetter heute?", "expected": []},
    {"id": "n-08", "kind": "no-answer", "lang": "zh", "query": "你们卖电视吗？", "expected": []},
]
