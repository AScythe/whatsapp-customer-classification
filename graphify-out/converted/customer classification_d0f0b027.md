<!-- converted from customer classification.docx -->

To classify users interacting with your WhatsApp product campaign, group them by their intent and readiness to buy. [1, 2]
Here is a 4-tier hierarchical classification system designed for WhatsApp's conversational format:
Tier 1: Hot Leads (Immediate Revenue)
High intent users who require instant responses to close the sale.
Cart Abandoners: Users who stopped mid-checkout after receiving product links.
Ready Buyers: Users explicitly asking "How do I pay?" or requesting invoices.
Promotion Seekers: Users trying to apply specific discount codes or campaign offers.
Tier 2: Warm Leads (High Consideration)
Interested users who need specific information or reassurance before buying.
Product Inquirers: Users asking about sizes, colors, materials, or specifications.
Logistics Checkers: Users asking about shipping costs, delivery times, or return policies.
Social Proof Seekers: Users asking for reviews, testimonials, or product warranties. [3]
Tier 3: Cold Leads (Low Intent / Engagement)
Users who interacted out of curiosity or by accident, requiring nurturing. [4, 5]
Window Shoppers: Users who replied with generic text like "Hello", "Nice", or emojis.
Misdirected Users: Users asking for products or services you do not offer.
Opt-Outs: Users requesting to stop receiving messages or typing "Stop". [6, 7, 8]
Tier 4: Support & Existing Customers (Post-Purchase)
Users redirecting the campaign message to solve existing issues.
Repeat Buyers: Current customers asking about complementary products.
Order Status Checkers: Users tracking an existing order rather than buying a new one.
Troubleshooters: Users complaining about a broken link, bug, or previous bad experience. [9, 10, 11]

To help you automate this classification, let me know:
What specific product or service are you promoting?
Do you want to build automated keyword rules or train an AI classifier?
What CRM or platform (e.g., HubSpot, ManyChat) holds your chat data?
I can provide the exact keywords or prompts to automatically sort these chats for you.

By condensing your structure into three tiers, you can absorb "Warm Leads" into Hot and Cold based on actionable intent. Users asking specific, high-intent questions move to Hot Leads, while users asking passive or broad questions move to Cold Leads. [1, 2]
Here is the revised 3-tier hierarchical classification system:
1. Hot Leads (High Intent & Immediate Action)
This tier includes ready buyers and warm leads who are actively evaluating specific product details to make a purchase decision today. [3, 4, 5, 6]
Ready Buyers: Users asking for payment links, invoices, or saying "I want to buy."
Specific Inquirers (Merged Warm): Users asking about specific sizes, stock availability, or pricing variations.
Logistics Checkers (Merged Warm): Users asking about shipping times, delivery locations, or return guarantees.
Cart Abandoners: Users who started the checkout process through the chat but stopped. [7, 8, 9, 10]
2. Cold Leads (Low Intent & Nurturing)
This tier includes low-engagement users and warm leads who are only seeking general information without a clear timeline to buy. [11, 12, 13, 14, 15]
General Inquirers (Merged Warm): Users asking broad questions like "How does this product work?" or "What do you sell?"
Social Proof Seekers (Merged Warm): Users asking for general reviews, photos, or browsing your catalog passively.
Casual Responders: Users replying with single words, greeting emojis, or automated quick-replies.
Opt-Outs: Users explicitly asking to be removed from the broadcast list. [16]
3. Existing Customers (Account & Support Management)
This tier isolates users who have already purchased from you, preventing sales messages from overlapping with customer service needs. [17]
Order Status Checkers: Users asking for tracking numbers, shipping updates, or delivery status.
Repeat Buyers: Previous customers asking about upgrades, refills, or complementary products.
Support Seekers: Users reporting issues with previous orders, broken links, or payment errors. [18]

To help you implement this 3-tier system, let me know:
Are your chat agents tagging these manually, or do you want to automate this with AI?
What specific product are you selling in this campaign?
Do you need help writing standard text templates for agents to reply to each tier?
I can give you the exact guidelines or automation rules to sort these leads immediately.

To automate this sorting using an AI classifier (like ChatGPT API or a WhatsApp bot tool) or basic keyword rules, use the following operational guidelines and matching logic.
1. AI Classifier Prompt (Recommended)
Copy and paste this prompt template into your AI system or LLM-based categorization tool:
You are a lead triage assistant analyzing WhatsApp chat transcripts from a product campaign. Classify the user into exactly one of three tiers: HOT_LEAD, COLD_LEAD, or EXISTING_CUSTOMER based on these rules:

1. HOT_LEAD: The user shows high intent or is evaluating specific details to buy right now. Look for:
- Requests for payment links, pricing variants, or bank details.
- Specific product availability questions (e.g., "Do you have size M in blue?").
- Delivery/shipping logistics for their specific location.
- Phrases indicating immediate interest (e.g., "Send me the invoice," "Can I order?").

2. EXISTING_CUSTOMER: The user already bought a product and has a post-purchase inquiry. Look for:
- Phrases indicating user already purchased a product.
- Tracking numbers or delivery status updates for a past order.
- Complaints about a defective item or payment issues from a previous purchase.
- Repeat purchase requests for accessories or refills.

2. COLD_LEAD: The user shows low intent, is browsing casually, or wants general information. Look for:
- Anything that doesn’t fit the criteria on HOT_LEAD or EXISTING_CUSTOMER
- Very broad product questions ("What is this?", "How does it work?").
- Requests for reviews or general proof without asking how to buy.
- Unsubscribe or rejection phrases ("Stop", "Not interested", "No thanks").

Analyze the following chat and return ONLY the JSON object: {"tier": "TIER_NAME", "reason": "1-sentence justification"}.
[INSERT CHAT TRANSCRIPT HERE]
2. Keyword-Based Automation Rules
If you are using a chatbot builder (like ManyChat, Landbot, or HubSpot) that relies on specific keywords, use these triggers:
Hot Leads Trigger Keywords [1]
Set these to assign a "Hot Lead" tag and instantly alert a live human sales agent. [2, 3, 4]
Payment Intent: "price", "how much", "cost", "buy", "order", "purchase", "pay", "bank", "link", "checkout", "invoice"
Specific Intent: "available", "stock", "size", "color", "in store", "ship to", "delivery time", "how long" [5, 6, 7]
Cold Leads Trigger Keywords [8]
Set these to trigger an automated educational flow or mark the chat as low priority. [9]
Passive Intent: "what is", "info", "details", "brochure", "catalog", "website", "just looking", "nice", "ok", "hello"
Opt-Out Intent: "stop", "unsubscribe", "remove", "no", "don't send", "not interested" [10, 11, 12]
Existing Customers Trigger Keywords
Set these to automatically route the chat away from sales and into your customer support queue. [13]
Post-Purchase: "status", "track", "where is my", "tracking", "delivered", "arrived", "received", "broken", "wrong item", "refund", "return" [14, 15]

To tailor this setup exactly to your current business workflow, tell me:
Which software platform (e.g., ManyChat, HubSpot, OpenAI API) are you using to run your WhatsApp automations?
Would you like me to draft automated template responses for each tier to save your team time? [16]

