# 📊 Tableau Advanced Interview Prep Sheet

A collection of **real-world scenario-based Tableau interview Q&A** with concise, to-the-point answers.  
Use this as a quick reference or GitHub-ready study guide.  

---

## 🔹 1. Dashboard Performance
**Q:** Dashboard takes 2 min to load — how to optimize?  
**A:** Use extracts, context filters, limit quick filters, reduce custom SQL, pre-aggregate in DB.  

---

## 🔹 2. Large Data Volumes
**Q:** Tableau crashes with 200M rows — solution?  
**A:** Use extracts with incremental refresh, aggregated summary tables, DB-side calculations.  

---

## 🔹 3. Row-Level Security (RLS)
**Q:** Show region-specific data per sales manager?  
**A:** Apply RLS using `USERNAME()`:  
```tableau
IF USERNAME()="manager1" THEN [Region]="East" END
