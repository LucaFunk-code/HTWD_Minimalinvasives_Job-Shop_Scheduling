# 3-Minuten Vortrag: Tabu Search für Job-Shop Scheduling

## ⏱️ Zeitplan

- **0:00 - 0:45** (45 Sek): Lokale Suchverfahren - Grundlagen
- **0:45 - 1:45** (60 Sek): Tabu Search - Funktionsweise
- **1:45 - 3:00** (75 Sek): Ergebnisse und Zielfunktionen

---

## 📝 Detaillierter Plan

### 1️⃣ Lokale Suchverfahren (0:00 - 0:45)

**Kernaussage:** Iterative Verbesserung durch Nachbarschaftssuche

**Inhalt:**
- **Problem:** Job-Shop Scheduling ist NP-schwer → exakte Verfahren zu langsam
- **Lösung:** Lokale Suchverfahren
  - Start mit einer Initiallösung
  - Iterative Verbesserung durch Nachbarschaftssuche
  - Bewegt sich im Lösungsraum durch kleine Änderungen
- **Problem der lokalen Suche:** Bleibt in lokalen Optima stecken
- **→ Überleitung:** Tabu Search löst dieses Problem

---

### 2️⃣ Tabu Search Funktionsweise (0:45 - 1:45)

**Kernaussage:** Vermeidung von Zyklen durch Tabu-Liste

**Inhalt:**

#### Grundprinzip:
- **Tabu-Liste:** Speichert verbotene Züge (kürzlich durchgeführte Operationen)
- **Erlaubt:** Verschlechterungen, um lokale Optima zu verlassen
- **Verhindert:** Zyklen und Rückkehr zu kürzlich besuchten Lösungen

#### Konkrete Implementierung:
1. **Initiallösung:** Zufällige Schedule-Generierung
2. **Nachbarschaftsoperator:** Swap-Operationen zwischen Jobs
3. **Tabu-Liste:** Feste Länge (z.B. 10-20), speichert verbotene Swaps
4. **Iterationen:** Feste Anzahl (z.B. 1000 Iterationen)
5. **Best-Solution-Tracking:** Speichert beste gefundene Lösung

#### Visualisierung (optional):
```
Initial → [Iteration 1] → [Iteration 2] → ... → [Iteration N]
            ↓ Swap           ↓ Swap                 ↓
         Tabu-Liste      Tabu-Liste           Beste Lösung
```

---

### 3️⃣ Ergebnisse (1:45 - 3:00)

**Kernaussage:** Zwei Zielfunktionen mit signifikanten Verbesserungen

#### A) Implementierte Zielfunktionen:

**1. Makespan-Minimierung (Standardziel)**
```
Ziel: Minimiere Cmax (Gesamtfertigstellungszeit)
```

**2. Termintreue-Optimierung (Lateness Deviation)**
```
Z = w_t × ΣTardiness + w_e × ΣEarliness + w_dev × ΣDeviation
```
- **Tardiness (Tj):** Verspätung gegenüber Due Date
- **Earliness (Ej):** Verfrühung
- **Deviation (Dev):** Abweichung vom ursprünglichen Plan
- **Gewichte:** Konfigurierbar (z.B. w_t=0.5, w_e=0.5, w_dev=0.3)

#### B) Ergebnisse:

**Verbesserungen:**
- ✅ Durchschnittliche Verbesserung: **~8-10%** der Zielfunktion
- ✅ Tracking von Initial- vs. Final-Makespan
- ✅ Pro-Shift-Analyse (z.B. 245 Operationen pro Schicht)

**Beispiel-Output:**
```
Shift 1: 5432 → 4891 (9.96% Verbesserung)
Shift 2: 6234 → 5678 (8.92% Verbesserung)
```

**Flexibilität:**
- ⚙️ Anpassbare Gewichte für unterschiedliche Prioritäten
- 📊 Analyse von Termintreue vs. Effizienz
- 🔄 Berücksichtigung von Planstabilität

---

## 🎯 Zusammenfassung (Abschluss-Satz)

> *"Tabu Search ermöglicht es, sowohl effiziente Makespan-Minimierung als auch termintreue Scheduling-Lösungen zu finden, mit durchschnittlichen Verbesserungen von 8-10% gegenüber zufälligen Initiallösungen."*

---

## 💡 Tipps für den Vortrag

### Visualisierungen (falls möglich):
1. **Folie 1:** Schema lokale Suche vs. globales Optimum
2. **Folie 2:** Tabu-Liste Prinzip (Zyklus-Vermeidung)
3. **Folie 3:** Ergebnis-Tabelle oder Balkendiagramm

### Wichtige Zahlen zum Merken:
- ✅ **~8-10%** durchschnittliche Verbesserung
- ✅ **2 Zielfunktionen** implementiert
- ✅ **3 Gewichte** in Termintreue-Funktion (w_t, w_e, w_dev)

### Mögliche Rückfragen vorbereiten:
1. "Wie groß ist die Tabu-Liste?" → Typisch 10-20
2. "Wie viele Iterationen?" → Z.B. 1000
3. "Wie lange dauert die Berechnung?" → Pro Shift ca. 12-15 Sekunden
4. "Welche Nachbarschaftsoperationen?" → Swap-Operationen zwischen Jobs

---

## 🔄 Alternative Struktur (falls mehr Tiefe gewünscht)

Falls du bei einem Punkt mehr ins Detail gehen möchtest, kannst du hier kürzen:
- **Kürzen:** Lokale Suche auf 30 Sek
- **Mehr Zeit für:** Ergebnisse (90 Sek) mit konkreten Zahlen und Diagrammen
