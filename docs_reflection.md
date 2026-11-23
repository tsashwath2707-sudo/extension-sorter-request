# Student Capstone Reflection: Extension Request Sorter

**Student Reflection Essay**  
**Course:** First-Year AI Capstone Project  
**Author:** AI Capstone Student  
**Word Count:** 398 words  

---

When I started this capstone project, I thought building an AI application just meant writing a prompt and letting a chatbot make the decisions. I assumed that if I described the university extension policy to a language model, it could easily read student emails and decide who gets an extension and who does not. However, actually designing and building the Extension Request Sorter completely changed my perspective on artificial intelligence and software engineering.

The biggest thing I learned is that AI models are great at reading natural language, but they should never make final administrative decisions on their own. Language models are probabilistic, meaning they guess the next words rather than following strict logic. In college administration, fairness and consistency are essential. When I tried red-team testing with adversarial prompt injections—like pretending to be the dean and commanding the AI to approve a request—I saw how easily a naive AI prompt could be tricked. I solved this by separating the AI from the decision logic. I used the AI only to extract information like the course code, days requested, and reason into JSON format. Then, I wrote pure Python code to validate the numbers and apply university rules. This hybrid approach made the system completely reliable and resistant to prompt injection attacks.

Another major challenge was student privacy. Real extension requests often mention sensitive medical conditions like surgeries, dengue, or personal distress. I realized that displaying these illnesses in general reports violates student privacy. To fix this, I created a Python privacy filter that removes specific illness names and keeps summaries short and generic. I also separated the output files so that general staff only see clean summaries, while professors get the raw text when making careful review decisions.

I tested the project thoroughly using mock mode, running five evaluation cases and three red-team security tests covering prompt injections, date traps, and fake course codes. The system defended against all of them successfully. 

Currently, the project has limitations. It processes CSV files rather than connecting directly to university email or canvas portals, and it cannot verify doctor certificates automatically. In the future, I want to add canvas integration and automated reply emails for missing information. Overall, this project taught me that trustworthy AI is about assisting teachers with routine sorting while keeping human judgment at the center.
