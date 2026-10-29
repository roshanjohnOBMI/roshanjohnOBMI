<a href="https://roshanjohnobmi.github.io/"><img src="assets/banner.svg" width="100%" alt="J K Roshan Kerketta — BIM Manager, Architect, Automation Developer. Play my 3D build site." /></a>

<p align="center">
  <a href="https://roshanjohnobmi.github.io/"><b>▶ Play the 3D build site</b></a> ·
  <a href="https://www.linkedin.com/in/j-k-roshan-kerketta-a2a4a669">LinkedIn</a> ·
  <a href="https://kuldeep3618x.github.io/roshan-cv/">CV</a>
</p>

Architect-turned-developer building automation tools, cloud platforms and data pipelines that make BIM delivery faster and more reliable. Ten years on airports, stadiums, high-rise towers and giga-projects, now at OBMI in Dubai.

*Dreaming, Developing, Deploying.*

---

## Focus

> **BIM Automation · Revit & Navisworks Add-ins · Autodesk Platform Services · Power Platform · AI Workflows**

## How the tools connect

<img src="assets/pipeline.svg" width="100%" alt="Revit and Navisworks models feed C# and pyRevit add-ins, which push data through APS and ACC into the Power Platform and out to dashboards. OBMI Meridian feeds usage and model health back." />

<details>
<summary><b>Open the workflows</b> (click a tool to expand)</summary>

<br>

<details>
<summary>🧭 <b>OBMI Meridian</b> — deploy, license and track every add-in</summary>

```mermaid
flowchart LR
  A[Sign in with Autodesk ID] --> B[Add-in catalogue]
  B --> C[Deploy to Revit]
  B --> D[Deploy to Navisworks]
  C --> E[(Usage telemetry)]
  D --> E
  E --> F[Admin dashboard]
```
</details>

<details>
<summary>🩺 <b>ACC Model Health Check</b></summary>

```mermaid
flowchart LR
  A[ACC hub] --> B[Pull models via APS] --> C[Run checks] --> D[Health score] --> E[Report]
```
</details>

<details>
<summary>📋 <b>TIDP / MIDP Checker</b></summary>

```mermaid
flowchart LR
  A[Delivery plan] --> C{Match & compare}
  B[ACC deliverables] --> C
  C --> D[Gaps flagged] --> E[Status report]
```
</details>

<details>
<summary>🧱 <b>Workset Manager</b> (pyRevit)</summary>

```mermaid
flowchart LR
  A[Excel rules] --> B[Match by category & family] --> C[Preview in WPF] --> D[Bulk assign] --> E[Clean model]
```
</details>

<details>
<summary>💬 <b>ClashCommentSync</b> · ⚙️ <b>Clash Tolerance Updater</b> (Navisworks)</summary>

```mermaid
flowchart LR
  subgraph Comments
    A[Clash results] --> B[Export to Excel] --> C[Team comments] --> D[Import back]
  end
  subgraph Tolerance
    E[Select tests] --> F[Copy] --> G[Edit tolerance] --> H[Commit]
  end
```
</details>

<details>
<summary>📊 <b>ACC → Power BI Live Data</b></summary>

```mermaid
flowchart LR
  A[Revit model on ACC] --> B[Data Exchange GraphQL] --> C[Power Query Online] --> D[Dataflow refresh] --> E[Live dashboard]
```
</details>

</details>

## Tools

<img src="assets/stack-helix.svg" width="100%" alt="Tech stack as a rotating double helix: Revit API, Navisworks API, pyRevit, Dynamo, C#/.NET, Python, JavaScript/Node.js, TypeScript, Autodesk Platform Services, ACC, GraphQL/REST, Azure, Power BI, Power Automate, Power Apps, Power Query, ClosedXML, SharePoint." />

## Work

| Name | Description | Link | Status | Tech Stack |
| --- | --- | --- | --- | --- |
| OBMI Meridian | Command centre for OBMI's BIM data — add-in deployment, shared credentials and usage tracking | Internal | Work in Progress | Node.js · Express · APS · Azure |
| ACC Model Health Check | Automated health reporting for Revit models on Autodesk Construction Cloud | Internal | Completed | Node.js · APS |
| TIDP / MIDP Checker | Checks information delivery plans against ACC deliverables | Internal | Completed | Node.js · APS |
| Workset Manager | pyRevit extension for bulk element-to-workset assignment with Excel rules | Internal | Completed | Python · pyRevit · WPF |
| ClashCommentSync | Navisworks add-in to round-trip clash comments through Excel | Internal | Completed | C# · Navisworks API · ClosedXML |
| Clash Tolerance Updater | Bulk clash-test tolerance updates through the Navisworks Clash API | Internal | Completed | C# · Navisworks API |
| ACC → Power BI Live Data | Live Revit data in Power BI Online via the APS Data Exchange GraphQL API | Internal | Completed | Power Query M · GraphQL · APS |
| OBMI Move30 | Web app for OBMI's 30x30 Wellness Challenge with Microsoft 365 sign-in and wearable sync | Internal | Work in Progress | React · PWA · Microsoft 365 |
| obmiAppCosting | Costing app for OBMI applications | [GitHub](https://github.com/roshanjohnOBMI/obmiAppCosting) | Completed | TypeScript |
| Roshan's Build Site | This profile as a playable 3D construction site | [Play](https://roshanjohnobmi.github.io/) | Live | Three.js · WebGL |

## Projects I've delivered on

> NEOM Trojena · Al Maktoum International Airport · Bin Rashid Stadium · Ras El Hekmah · Wadi Yemm

---

## Site progress

<img src="assets/site-stats.svg" width="100%" alt="Site progress board: public contributions per month as an isometric skyline, with contribution, commit, repository and streak counters and a language breakdown. Updated nightly." />

## 3D contributions

<img src="profile-3d-contrib/profile-night-rainbow.svg" width="100%" alt="3D contribution calendar" />

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/roshanjohnOBMI/roshanjohnOBMI/output/github-snake-dark.svg" />
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/roshanjohnOBMI/roshanjohnOBMI/output/github-snake.svg" />
  <img alt="Contribution snake" src="https://raw.githubusercontent.com/roshanjohnOBMI/roshanjohnOBMI/output/github-snake-dark.svg" width="100%" />
</picture>
