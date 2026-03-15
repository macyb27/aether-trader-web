# Aether Trader Pro - Live-Setup Guide

Dieser Guide beschreibt die notwendigen Schritte und Konfigurationen, um das Aether Trader Pro System von einer Entwicklungsumgebung in einen produktionsreifen Live-Betrieb zu überführen. Er konzentriert sich auf die externen Abhängigkeiten und Benutzereingaben, die außerhalb des Code-Deployments liegen.

---

## 1. Externe Konten & Services

Für den Live-Betrieb sind Anbindungen an externe Dienste unerlässlich. Stellen Sie sicher, dass Sie die folgenden Konten eingerichtet und die entsprechenden Zugangsdaten bereit haben:

| Service | Zweck | Details & Hinweise |
|---------|-------|--------------------|
| **Broker/Exchange** | Live-Handel, Order-Ausführung | Wählen Sie einen Broker, der eine robuste API (REST & WebSocket) anbietet. Beispiele: Binance, Kraken, Interactive Brokers, Alpaca. Stellen Sie sicher, dass Sie ein **Live-Handelskonto** (nicht nur Paper Trading) mit ausreichender Finanzierung haben. |
| **Marktdaten-Anbieter** | Echtzeit- und historische Daten | Für kritische Echtzeitdaten empfiehlt sich ein professioneller Anbieter (z.B. Polygon.io, Xignite, Refinitiv). Für historische Daten können auch yfinance oder CCXT verwendet werden, aber für Live-Systeme ist eine dedizierte, zuverlässige Quelle vorzuziehen. |
| **Cloud Provider** | Hosting der Infrastruktur | AWS, Google Cloud (GCP) oder Azure. Sie benötigen ein aktives Konto mit ausreichenden Berechtigungen für Kubernetes, Datenbanken, Storage und Netzwerkdienste. |
| **Sentry.io** | Fehler-Tracking & Performance-Monitoring | Ein Sentry-Konto zur Überwachung der Anwendung in Produktion. Sie benötigen den DSN (Data Source Name). |
| **Cloudflare (optional)** | DDoS-Schutz, CDN, DNS | Für zusätzliche Sicherheit und Performance des Frontends und der API. |

---

## 2. Umgebungsvariablen (Environment Variables)

Alle sensiblen Daten und Konfigurationen werden über Umgebungsvariablen verwaltet. Diese müssen in Ihrer Produktionsumgebung (z.B. Kubernetes Secrets, Docker Compose `.env` Datei, Cloud Provider Secret Manager) gesetzt werden.

Eine vollständige Liste finden Sie in der `.env.example` Datei im Root-Verzeichnis des Projekts. Hier sind die kritischsten Variablen, die Sie anpassen müssen:

| Variable | Beschreibung | Beispielwert | Hinweise |
|----------|--------------|--------------|----------|
| `AETHER_ENV` | Umgebung (production, development) | `production` | Steuert Logging-Verhalten, Debug-Modus etc. |
| `AETHER_MASTER_KEY` | **Kritisch:** Hauptschlüssel für die Verschlüsselung sensibler Daten | `YOUR_VERY_STRONG_32_BYTE_KEY` | **MUSS** ein sicherer, zufälliger 32-Byte-Schlüssel sein. In Produktion in einem KMS (AWS KMS, GCP KMS, HashiCorp Vault) speichern. |
| `DATABASE_URL` | PostgreSQL-Verbindungsstring | `postgresql+asyncpg://user:password@host:5432/aether_db` | Ersetzen Sie `user`, `password`, `host` und `aether_db` durch Ihre Produktionsdatenbank-Details. |
| `REDIS_URL` | Redis-Verbindungsstring | `redis://:password@host:6379/0` | Ersetzen Sie `password` und `host`. |
| `SENTRY_DSN` | Sentry Data Source Name | `https://examplepublickey@o0.ingest.sentry.io/0` | Von Ihrem Sentry.io-Projekt. |
| `CCXT_EXCHANGE_ID` | ID der verwendeten Börse für CCXT | `binance` | Entspricht der ID in CCXT. |
| `CCXT_API_KEY` | API-Schlüssel für die Börse | `YOUR_EXCHANGE_API_KEY` | **Wird mit `AETHER_MASTER_KEY` verschlüsselt.** |
| `CCXT_SECRET_KEY` | Secret Key für die Börse | `YOUR_EXCHANGE_SECRET_KEY` | **Wird mit `AETHER_MASTER_KEY` verschlüsselt.** |
| `YFINANCE_ENABLED` | yfinance Datenquelle aktivieren | `false` | Für Live-Betrieb oft nicht empfohlen, da nicht echtzeitfähig. |
| `ALPACA_API_KEY` | Alpaca API Key (falls verwendet) | `YOUR_ALPACA_API_KEY` | **Wird mit `AETHER_MASTER_KEY` verschlüsselt.** |
| `ALPACA_SECRET_KEY` | Alpaca Secret Key (falls verwendet) | `YOUR_ALPACA_SECRET_KEY` | **Wird mit `AETHER_MASTER_KEY` verschlüsselt.** |
| `ALPACA_PAPER_TRADING` | Alpaca Paper Trading Modus | `false` | Für Live-Handel auf `false` setzen. |
| `LIVE_TRADING_ENABLED` | Live-Handel aktivieren | `true` | **Vorsicht!** Nur aktivieren, wenn alle Checks bestanden sind. |
| `RISK_MAX_DAILY_LOSS` | Maximaler täglicher Verlust (Prozentsatz) | `0.01` (1%) | Wichtige Risikoparameter. |
| `RISK_MAX_POSITION_SIZE` | Maximale Positionsgröße (Prozentsatz des Portfolios) | `0.05` (5%) | |
| `RISK_MAX_PORTFOLIO_LEVERAGE` | Maximaler Portfolio-Hebel | `1.0` (kein Hebel) | |

---

## 3. How-To: Schritt-für-Schritt-Anleitung für den Live-Betrieb

Befolgen Sie diese Schritte, um Ihr Aether Trader Pro System in Produktion zu bringen:

### Schritt 1: Cloud-Infrastruktur vorbereiten

1.  **Cloud Provider wählen & Konto einrichten**: Entscheiden Sie sich für AWS, GCP oder Azure und richten Sie ein Konto ein. Stellen Sie sicher, dass Sie die notwendigen Berechtigungen haben.
2.  **Kubernetes Cluster bereitstellen**: Erstellen Sie einen Managed Kubernetes Cluster (EKS, GKE, AKS). Konfigurieren Sie die Worker Nodes mit ausreichenden Ressourcen (CPU, RAM).
3.  **Datenbanken bereitstellen**: Erstellen Sie eine Managed PostgreSQL-Instanz und eine Managed Redis-Instanz. Stellen Sie sicher, dass diese über private Netzwerke (VPC) erreichbar sind und hochverfügbar konfiguriert sind (Multi-AZ, Replikation).
4.  **Secret Manager einrichten**: Konfigurieren Sie einen Secret Manager (z.B. AWS Secrets Manager, GCP Secret Manager, HashiCorp Vault) zur sicheren Speicherung des `AETHER_MASTER_KEY` und anderer sensibler Umgebungsvariablen.

### Schritt 2: Code & Konfiguration anpassen

1.  **`.env.example` anpassen**: Füllen Sie die `.env.example` Datei mit den tatsächlichen Werten Ihrer Produktionsumgebung aus (API-Keys, Datenbank-URLs, Sentry DSN etc.). **WICHTIG:** Der `AETHER_MASTER_KEY` muss ein sehr starker, zufälliger Schlüssel sein.
2.  **API-Keys verschlüsseln**: Nutzen Sie das `backend/utils/security.py` Modul, um Ihre `CCXT_API_KEY`, `CCXT_SECRET_KEY`, `ALPACA_API_KEY`, `ALPACA_SECRET_KEY` etc. zu verschlüsseln. Das Skript kann lokal ausgeführt werden, um die verschlüsselten Werte zu generieren, die dann in die Umgebungsvariablen (z.B. Kubernetes Secrets) eingetragen werden:
    ```bash
    # Beispiel: Verschlüsseln Sie Ihren CCXT_API_KEY
    python -c "from backend.utils.security import secrets; print(secrets.encrypt('YOUR_RAW_CCXT_API_KEY'))"
    # Den Output als Wert für CCXT_API_KEY in Ihrer Produktionsumgebung setzen.
    ```
3.  **Alembic-Migrationen durchführen**: Initialisieren und wenden Sie die Datenbank-Migrationen an, um das Datenbankschema zu erstellen oder zu aktualisieren:
    ```bash
    # Innerhalb des Backend-Containers oder auf einer Maschine mit DB-Zugriff
    alembic revision --autogenerate -m "Initial migration"
    alembic upgrade head
    ```

### Schritt 3: Deployment & Start

1.  **CI/CD-Pipeline konfigurieren**: Richten Sie Ihre CI/CD-Pipeline (z.B. GitHub Actions) so ein, dass sie bei Änderungen am `master` oder `main` Branch automatisch die Docker-Images baut, testet und in Ihre Container Registry (z.B. Docker Hub, ECR, GCR) pusht.
2.  **Kubernetes Deployment**: Wenden Sie die aktualisierten Kubernetes-Manifeste aus dem `infrastructure/kubernetes/` Verzeichnis auf Ihren Cluster an. Stellen Sie sicher, dass die Umgebungsvariablen (insbesondere die verschlüsselten Secrets) korrekt als Kubernetes Secrets konfiguriert sind.
    ```bash
    kubectl apply -f infrastructure/kubernetes/namespace.yml
    kubectl apply -f infrastructure/kubernetes/secrets.yml # Stellen Sie sicher, dass Ihre Secrets hier korrekt sind
    kubectl apply -f infrastructure/kubernetes/backend-deployment.yml
    kubectl apply -f infrastructure/kubernetes/frontend-deployment.yml
    # ... weitere Deployments (Prometheus, Grafana, Airflow)
    ```
3.  **Airflow DAGs deployen**: Laden Sie die Airflow DAGs aus `infrastructure/airflow/dags/` in Ihre Airflow-Umgebung hoch und aktivieren Sie sie. Stellen Sie sicher, dass die DAGs die korrekten Umgebungsvariablen für den Live-Betrieb verwenden.

### Schritt 4: Monitoring & Validierung

1.  **Sentry-Integration prüfen**: Überprüfen Sie Ihr Sentry-Dashboard, ob Fehler und Performance-Daten korrekt erfasst werden.
2.  **Grafana-Dashboards**: Importieren Sie die Grafana-Dashboards (`infrastructure/grafana/dashboards/aether-trading.json`) in Ihre Grafana-Instanz und stellen Sie sicher, dass alle Metriken korrekt angezeigt werden.
3.  **Health Checks**: Überwachen Sie die `/health` Endpunkte Ihrer FastAPI-Anwendung und die Kubernetes Liveness/Readiness Probes.
4.  **Manuelle Überprüfung**: Beginnen Sie mit einem sehr kleinen Handelsvolumen und überwachen Sie die ersten Trades genau. Vergleichen Sie die Ausführungen mit Ihrem Broker-Konto.

---

## 4. Wichtige Hinweise für den Live-Betrieb

*   **Start klein**: Beginnen Sie immer mit dem kleinstmöglichen Handelsvolumen und erhöhen Sie es schrittweise, sobald Sie Vertrauen in das System gewonnen haben [1].
*   **Psychologie**: Der Übergang vom Paper Trading zum Live-Handel ist auch eine psychologische Herausforderung. Bleiben Sie diszipliniert und halten Sie sich an Ihre Strategie und Risikolimits [2].
*   **Notfallplan**: Haben Sie immer einen Notfallplan (Kill Switch) bereit, um das System im Falle unerwarteter Probleme sofort stoppen zu können. Der `LiveRiskEngine` bietet hierfür Funktionen.
*   **Regelmäßige Wartung**: Planen Sie regelmäßige Updates, Patches und Performance-Reviews ein.

---

**Autor**: Manus AI
**Datum**: 15. März 2026
**Version**: 1.0

---

## Referenzen

[1] Going to switch from paper trading to real trading. Any tips ... (n.d.). *Reddit*. [https://www.reddit.com/r/Daytrading/comments/vabrvl/going_to_switch_from_paper_trading_to_real/](https://www.reddit.com/r/Daytrading/comments/vabrvl/going_to_switch_from_paper_trading_to_real/)
[2] The Complete Guide to Transitioning from Demo to Live Trading. (n.d.). *Medium*. [https://ultimamarkets.medium.com/the-complete-guide-to-transitioning-from-demo-to-live-trading-3b375e97a870](https://ultimamarkets.medium.com/the-complete-guide-to-transitioning-from-demo-to-live-trading-3b375e97a870)
