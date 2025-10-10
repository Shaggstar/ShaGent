import { App, MarkdownView, Notice, Plugin, PluginSettingTab, Setting, TFile } from 'obsidian';
import { SupabaseClient } from '@supabase/supabase-js';
import { BetterSelfSettings, DEFAULT_SETTINGS } from './settings';
import { initSupabaseClient } from './api/supabase';

export default class BetterSelfPlugin extends Plugin {
  settings: BetterSelfSettings;
  supabase: SupabaseClient | null = null;

  async onload() {
    await this.loadSettings();

    if (this.settings.supabaseUrl && this.settings.supabaseKey) {
      this.supabase = initSupabaseClient(this.settings.supabaseUrl, this.settings.supabaseKey);
    }

    this.addRibbonIcon('calendar-check', 'Better Self: Morning Check-In', () => {
      this.createMorningCheckIn();
    });

    this.addCommand({
      id: 'morning-check-in',
      name: 'Create Morning Check-In',
      callback: () => this.createMorningCheckIn(),
    });

    this.addCommand({
      id: 'evening-review',
      name: 'Create Evening Review',
      callback: () => this.createEveningReview(),
    });

    this.addCommand({
      id: 'generate-tasks',
      name: "Generate Today's Tasks (AI)",
      callback: () => this.generateTasks(),
    });

    this.addCommand({
      id: 'open-focus-session',
      name: 'Start Focus Session',
      callback: () => this.openFocusSession(),
    });

    this.addCommand({
      id: 'open-interview-practice',
      name: 'Practice Interview',
      callback: () => this.openInterviewPractice(),
    });

    this.addSettingTab(new BetterSelfSettingTab(this.app, this));
  }

  async loadSettings() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
  }

  async saveSettings() {
    await this.saveData(this.settings);

    if (this.settings.supabaseUrl && this.settings.supabaseKey) {
      this.supabase = initSupabaseClient(this.settings.supabaseUrl, this.settings.supabaseKey);
    } else {
      this.supabase = null;
    }
  }

  async createMorningCheckIn() {
    const date = window.moment().format('YYYY-MM-DD');
    const filePath = `Daily/${date}.md`;

    let file = this.app.vault.getAbstractFileByPath(filePath);
    if (!file) {
      const template = await this.getMorningTemplate(date);
      file = await this.app.vault.create(filePath, template);
      new Notice('📅 Morning check-in created!');
    }

    const leaf = this.app.workspace.getLeaf();
    await leaf.openFile(file as TFile);
  }

  async getMorningTemplate(date: string): Promise<string> {
    let models = ['Researcher', 'Career Builder', 'Poet', 'Parent'];

    if (this.supabase) {
      const { data, error } = await this.supabase
        .from('temporal_models')
        .select('name')
        .order('name');

      if (!error && data && data.length > 0) {
        models = data.map((m) => m.name as string);
      }
    }

    return `---
date: ${date}
temporal_model: 
energy: 
mood: 
tasks: []
---

# Morning Check-In

**Date**: ${date}

## Which self is needed today?

${models.map((m) => `- [ ] ${m}`).join('\n')}

## Energy & Mood

- **Energy**: ⚡️⚡️⚡️⚡️⚡️ (Rate 1-5)
- **Mood**: [Describe how you're feeling]

## Top 3 Priorities

<!-- Click "Generate Tasks" or add manually -->

1. [ ] 
2. [ ] 
3. [ ] 

## Focus Sessions Scheduled

- 9:00 - 10:30 AM: 
- 11:00 - 12:30 PM: 
- 2:00 - 3:30 PM: 

## Quick Win

[One 5-minute task to build momentum]

---

## Notes

[Space for thoughts, ideas, links]

---

## Evening Review

### Completed Today

- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

### Coherence: __/10

Did today's actions align with my values and temporal model?

### Reflection

**What went well:**

**What was challenging:**

**One thing to do differently tomorrow:**

### Gratitude

`;
  }

  async createEveningReview() {
    const date = window.moment().format('YYYY-MM-DD');
    const filePath = `Daily/${date}.md`;
    const file = this.app.vault.getAbstractFileByPath(filePath);

    if (!file) {
      new Notice('⚠️ Create a morning check-in first!');
      return;
    }

    const leaf = this.app.workspace.getLeaf();
    await leaf.openFile(file as TFile);

    const view = this.app.workspace.getActiveViewOfType(MarkdownView);
    if (view) {
      const editor = view.editor;
      const content = editor.getValue();
      const eveningIndex = content.indexOf('## Evening Review');

      if (eveningIndex !== -1) {
        const line = editor.offsetToPos(eveningIndex).line;
        editor.setCursor(line + 3);
      }
    }

    new Notice('📝 Evening review ready!');
  }

  async generateTasks() {
    if (!this.supabase) {
      new Notice('⚠️ Configure Supabase in settings first!');
      return;
    }

    try {
      new Notice('🤖 Generating tasks...');

      const file = this.app.workspace.getActiveFile();
      if (!file) {
        new Notice('⚠️ Open a daily note first!');
        return;
      }

      const cache = this.app.metadataCache.getFileCache(file);
      const frontmatter = cache?.frontmatter || {};

      const temporalModel = frontmatter.temporal_model || 'general';
      const energyLevel = frontmatter.energy || 3;

      const { data: goals, error: goalsError } = await this.supabase
        .from('goals')
        .select('*')
        .eq('temporal_model', temporalModel)
        .eq('status', 'active');

      if (goalsError) {
        throw goalsError;
      }

      const response = await fetch(`${this.settings.webAppUrl}/api/generate-tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          goals: goals || [],
          timeAvailable: 8,
          energyLevel,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate tasks');
      }

      const data = await response.json();
      const tasks = data.tasks || [];

      const view = this.app.workspace.getActiveViewOfType(MarkdownView);
      if (view) {
        const editor = view.editor;
        const content = editor.getValue();
        const prioritiesIndex = content.indexOf('## Top 3 Priorities');

        if (prioritiesIndex !== -1) {
          const insertLine = editor.offsetToPos(prioritiesIndex).line + 3;
          const taskList = tasks
            .slice(0, 3)
            .map((t: any, i: number) => `${i + 1}. [ ] ${t.title} (${t.minutes}m) #${t.energy}`)
            .join('\n');

          editor.replaceRange(taskList, { line: insertLine, ch: 0 });
        }
      }

      new Notice(`✅ Generated ${tasks.length} tasks!`);
    } catch (error) {
      console.error('Error generating tasks:', error);
      new Notice('❌ Failed to generate tasks. Check console for details.');
    }
  }

  openFocusSession() {
    window.open(`${this.settings.webAppUrl}/focus`, '_blank');
    new Notice('🎯 Opening focus session...');
  }

  openInterviewPractice() {
    window.open(`${this.settings.webAppUrl}/interview`, '_blank');
    new Notice('🎤 Opening interview practice...');
  }
}

class BetterSelfSettingTab extends PluginSettingTab {
  plugin: BetterSelfPlugin;

  constructor(app: App, plugin: BetterSelfPlugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display(): void {
    const { containerEl } = this;
    containerEl.empty();

    containerEl.createEl('h2', { text: 'Better Self Settings' });

    new Setting(containerEl)
      .setName('Supabase URL')
      .setDesc('Your Supabase project URL')
      .addText((text) =>
        text
          .setPlaceholder('https://xxxxx.supabase.co')
          .setValue(this.plugin.settings.supabaseUrl)
          .onChange(async (value) => {
            this.plugin.settings.supabaseUrl = value;
            await this.plugin.saveSettings();
          }),
      );

    new Setting(containerEl)
      .setName('Supabase API Key')
      .setDesc('Your Supabase anon/public key')
      .addText((text) =>
        text
          .setPlaceholder('eyJhbGc...')
          .setValue(this.plugin.settings.supabaseKey)
          .onChange(async (value) => {
            this.plugin.settings.supabaseKey = value;
            await this.plugin.saveSettings();
          }),
      );

    new Setting(containerEl)
      .setName('Web App URL')
      .setDesc('URL of the Better Self web application')
      .addText((text) =>
        text
          .setPlaceholder('http://localhost:3000')
          .setValue(this.plugin.settings.webAppUrl)
          .onChange(async (value) => {
            this.plugin.settings.webAppUrl = value;
            await this.plugin.saveSettings();
          }),
      );
  }
}
