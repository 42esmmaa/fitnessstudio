# Architektur

Die ausführliche Beschreibung steht in `docs/fitnessstudio.adoc`. Die Diagramme
werden mit PlantUML aus `docs/diagramme/*.puml` erzeugt.

## Schichten

Router (REST) bzw. GraphQL-Schema → Service (Geschäftslogik) → Repository
(SQLAlchemy) → PostgreSQL. Die Security-Schicht prüft Token und Rollen mit Keycloak.

![Schichtenarchitektur](img/schichtenarchitektur.svg)

## Laufzeitumgebung

![Komponenten](img/komponenten.svg)

## Datenmodell

![ER-Diagramm](img/er-diagramm.svg)

## Neues Mitglied anlegen

![Sequenzdiagramm Anlegen](img/sequenz-anlegen.svg)

## Mitglied ändern

![Sequenzdiagramm Ändern](img/sequenz-aendern.svg)
