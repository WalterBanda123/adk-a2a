# 🏪 Store Agent System

A sophisticated AI-powered business assistant system for informal traders in Zimbabwe, built with Google ADK's native sub-agent architecture.

## 🎯 Overview

This system uses a **coordinator pattern** with specialized sub-agents to help small business owners, shopkeepers, and vendors manage their daily operations, accounts, and business strategies effectively.

## 🏗️ Architecture

### Main Coordinator Agent

- **File:** `agents/assistant/agent.py`
- **Role:** Intelligent request router and coordinator
- **Strategy:** Delegates requests to specialized sub-agents based on domain expertise

### Specialized Sub-Agents

| Sub-Agent                  | Domain            | Responsibilities                                                |
| -------------------------- | ----------------- | --------------------------------------------------------------- |
| 👋 **User Greeting**       | Personalization   | Greetings, profile management, language preferences             |
| 💰 **Misc Transactions**   | Cash Operations   | Petty cash, deposits, owner drawings, product withdrawals       |
| 📊 **Financial Reporting** | Business Analysis | Reports, profit/loss statements, trend analysis                 |
| 🛍️ **Product Management**  | Inventory         | Product catalog, stock levels, pricing, reorder recommendations |
| 🤝 **Customer Service**    | General Support   | Business guidance, system help, strategy advice                 |

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Google ADK
- Firebase account (for data storage)
- Environment variables configured

### Installation

1. **Clone and navigate to the project:**

   ```bash
   cd /Users/walterbanda/Desktop/AI/adk-a2a/store-agents
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file with:

   ```
   GOOGLE_API_KEY=your_google_api_key
   FIREBASE_PROJECT_ID=your_firebase_project_id
   ```

4. **Configure Firebase:**
   Place your `firebase-service-account-key.json` in the project root.

### Running the System

```bash
python -m agents.assistant
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Test all sub-agents
python tests/test_all_subagents.py

# Test product withdrawal functionality
python tests/test_product_withdrawal_issue.py

# Test complete flow
python tests/test_complete_flow.py
```

## 📁 Project Structure

```
store-agents/
├── agents/assistant/           # Main agent and sub-agents
│   ├── agent.py               # 🎛️ Main coordinator
│   ├── misc_transactions_subagent.py      # 💰 Cash operations
│   ├── financial_reporting_subagent.py    # 📊 Reports
│   ├── product_management_subagent.py     # 🛍️ Inventory
│   ├── user_greeting_subagent.py          # 👋 Personalization
│   ├── customer_service_subagent.py       # 🤝 Support
│   ├── task_manager.py        # 🔧 Task coordination
│   └── tools/                 # 🛠️ Shared tools
├── common/                    # Shared services
│   ├── user_service.py
│   ├── product_service.py
│   ├── financial_service.py
│   └── misc_transactions_service.py
├── tests/                     # Test suite
├── docs/                      # Documentation
├── data/                      # Data storage
└── reports/                   # Generated reports
```

## 🎯 Key Features

### ✅ **Intelligent Delegation**

- Automatic routing to appropriate specialists
- Context-aware request handling
- Seamless user experience

### ✅ **Product Withdrawal Recognition**

- Owner drawing calculations
- Cash balance validation
- Product price inquiries

### ✅ **Multilingual Support**

- English, Shona, and Ndebele
- Zimbabwean business context
- Local currency and practices

### ✅ **Comprehensive Reporting**

- PDF financial reports
- Business performance analysis
- Trend analysis and recommendations

## 🔧 Development

### Adding New Sub-Agents

1. Create new sub-agent file in `agents/assistant/`
2. Implement using Google ADK Agent class
3. Add import and instantiation in `agent.py`
4. Update delegation patterns in main agent instructions

### Testing Guidelines

- Each sub-agent should have specific test cases
- Maintain 85%+ success rate for delegation
- Test critical business logic (owner drawings, cash operations)

## 📖 Documentation

- **Architecture Overview:** `docs/REFACTORING_COMPLETE.md`
- **Financial Reporting:** `docs/FINANCIAL_REPORT_TOOL.md`
- **Transactions Agent:** `docs/MISC_TRANSACTIONS_AGENT.md`

## 🌟 Success Metrics

- **Test Success Rate:** 87.5% (7/8 specialized domains)
- **Architecture:** Fully modular sub-agent system
- **Business Logic:** All critical functionality preserved
- **User Experience:** Seamless delegation and coordination

## 🔮 Future Enhancements

- Additional sub-agents for specific business domains
- Enhanced reporting capabilities
- Mobile app integration
- Advanced analytics and insights

## 📞 Support

For issues and questions:

- Check the documentation in `docs/`
- Run the test suite to validate functionality
- Review the refactoring completion report

---

**Built with ❤️ for Zimbabwean informal traders**
