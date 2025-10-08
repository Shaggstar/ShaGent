// main.ts
import { App, Plugin, PluginSettingTab, Setting, Notice, MarkdownView } from "obsidian";

interface CoachSettings {
  apiKey: string;
  targetMode: "audience" | "seo";
  targetDetail: string;
}

const DEFAULT_SETTINGS: CoachSettings = {
  apiKey: "",
  targetMode: "audience",
  targetDetail: "general readers"
};

export default class CoachPlugin extends Plugin {
  settings: CoachSettings;

  async onload() {
    await this.loadSettings();

    this.addCommand({
      id: "analyze-current-note",
      name: "Analyze current note",
      callback: () => this.runAnalysis()
    });

    this.addSettingTab(new CoachSettingTab(this.app, this));
  }

  async runAnalysis() {
    const view = this.app.workspace.getActiveViewOfType(MarkdownView);
    if (!view) { new Notice("Open a Markdown note first."); return; }
    const editor = view.editor;
    const text = editor.getValue();

    const payload = {
      mode: this.settings.targetMode,
      targetDetail: this.settings.targetDetail,
      kind: "auto",
      text
    };

    try {
      // Replace with your API endpoint
      const res = await fetch("http://localhost:9999/api/writing", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${this.settings.apiKey}`
        },
        body: JSON.stringify({ prompt: payload })
      });
      const raw = await res.text();
      const start = raw.indexOf("{");
      const end = raw.lastIndexOf("}");
      const json = JSON.parse(raw.slice(start, end + 1));
      const layers = json.layers || {};

      const summary =
        `\n> Coach: G:${layers.grammar?.score ?? "-"} ` +
        `C:${layers.clarity?.score ?? "-"} S:${layers.style?.score ?? "-"} ` +
        `K:${layers.content?.score ?? "-"} T:${layers.target?.score ?? "-"}\n`;

      editor.replaceRange(summary, { line: 0, ch: 0 });
      new Notice("Analysis complete.");
    } catch (e) {
      console.error(e);
      new Notice("Analysis failed. Check API key or endpoint.");
    }
  }

  onunload() {}

  async loadSettings() { this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData()); }
  async saveSettings() { await this.saveData(this.settings); }
}

class CoachSettingTab extends PluginSettingTab {
  plugin: CoachPlugin;
  constructor(app: App, plugin: CoachPlugin) {
    super(app, plugin);
    this.plugin = plugin;
  }
  display(): void {
    const { containerEl } = this;
    containerEl.empty();
    containerEl.createEl("h2", { text: "Writing Coach Settings" });

    new Setting(containerEl)
      .setName("API key")
      .setDesc("Model provider key")
      .addText(t => t
        .setPlaceholder("sk-...")
        .setValue(this.plugin.settings.apiKey)
        .onChange(async (v) => { this.plugin.settings.apiKey = v; await this.plugin.saveSettings(); }));

    new Setting(containerEl)
      .setName("Target mode")
      .setDesc("Audience or SEO")
      .addDropdown(d => d
        .addOption("audience", "Audience")
        .addOption("seo", "SEO")
        .setValue(this.plugin.settings.targetMode)
        .onChange(async (v: "audience" | "seo") => { this.plugin.settings.targetMode = v; await this.plugin.saveSettings(); }));

    new Setting(containerEl)
      .setName("Target detail")
      .setDesc("Audience description or keywords")
      .addText(t => t
        .setPlaceholder("ex: policy makers | or: active inference, narrative, semiotics")
        .setValue(this.plugin.settings.targetDetail)
        .onChange(async (v) => { this.plugin.settings.targetDetail = v; await this.plugin.saveSettings(); }));
  }
}
