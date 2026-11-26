import Clutter from 'gi://Clutter';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import Pango from 'gi://Pango';
import St from 'gi://St';

import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';

export default class IslandLinux extends Extension {
    enable() {
        // launcher.json dibuat saat packaging; tidak mengeksekusi shell command.
        const file = this.dir.get_child('launcher.json');
        const [ok, contents] = file.load_contents(null);
        if (!ok)
            throw new Error('Konfigurasi launcher island-linux tidak terbaca');
        this._launcher = JSON.parse(new TextDecoder().decode(contents));
        if (!Array.isArray(this._launcher.argv) || this._launcher.argv.length !== 2 ||
            !this._launcher.argv.every(arg => typeof arg === 'string' && GLib.path_is_absolute(arg)))
            throw new Error('Launcher harus berisi path absolut Python dan island.py');

        this._clock = Main.panel.statusArea.dateMenu.container;
        this._parent = this._clock.get_parent();
        this._originalIndex = this._parent.get_children().indexOf(this._clock);
        this._group = new St.BoxLayout({style_class: 'island-clock-group'});
        this._label = new St.Label({text: 'Mencari media…', y_align: Clutter.ActorAlign.CENTER});
        this._label.clutter_text.ellipsize = Pango.EllipsizeMode.END;
        this._icon = new St.Icon({icon_name: 'audio-x-generic-symbolic', style_class: 'island-panel-icon'});
        const content = new St.BoxLayout({style_class: 'island-panel-content'});
        content.add_child(this._icon);
        content.add_child(this._label);
        this._button = new St.Button({
            style_class: 'island-media-button', child: content,
            can_focus: true, reactive: true, track_hover: true,
            accessible_name: 'Buka kartu media island-linux',
        });
        this._button.connect('clicked', () => this._openCard());
        this._parent.remove_child(this._clock);
        this._group.add_child(this._clock);
        this._group.add_child(this._button);
        this._parent.insert_child_at_index(this._group, this._originalIndex);
        this._alive = true;
        this._cancellable = new Gio.Cancellable();
        this._poll();
        this._timer = GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, 2, () => {
            this._poll();
            return GLib.SOURCE_CONTINUE;
        });
    }

    _poll() {
        if (!this._alive || this._inspect)
            return;
        try {
            const process = new Gio.Subprocess({
                argv: [...this._launcher.argv, '--inspect'],
                flags: Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE,
            });
            process.init(null);
            this._inspect = process;
            // I/O asinkron: Python dan akses D-Bus tidak memblokir Shell.
            process.communicate_utf8_async(null, this._cancellable, (source, result) => {
                try {
                    const [, stdout] = source.communicate_utf8_finish(result);
                    if (!this._alive)
                        return;
                    if (!source.get_successful())
                        throw new Error('Inspeksi MPRIS gagal');
                    const state = JSON.parse(stdout);
                    const active = Boolean(state.bus_name);
                    this._label.text = active ? state.title : 'Tidak ada media';
                    this._icon.icon_name = active
                        ? (state.playback_status === 'Playing' ? 'media-playback-start-symbolic' : 'media-playback-pause-symbolic')
                        : 'audio-x-generic-symbolic';
                    this._button.accessible_name = active
                        ? `Buka kartu media: ${state.title}, ${(state.artists ?? []).join(', ')}`
                        : 'Tidak ada media. Buka kartu island-linux';
                } catch (error) {
                    if (this._alive) {
                        this._label.text = 'Media terputus';
                        this._button.accessible_name = 'Media terputus. Buka kartu untuk detail';
                    }
                } finally {
                    if (this._inspect === source)
                        this._inspect = null;
                }
            });
        } catch (error) {
            this._label.text = 'Periksa instalasi';
            console.error(`island-linux: ${error.message}`);
        }
    }

    _openCard() {
        if (this._card)
            return;
        try {
            const process = new Gio.Subprocess({
                argv: [...this._launcher.argv, '--panel-card'],
                flags: Gio.SubprocessFlags.NONE,
            });
            process.init(null);
            this._card = process;
            process.wait_async(null, (source, result) => {
                try {
                    source.wait_finish(result);
                } catch (error) {
                    console.error(`island-linux: ${error.message}`);
                }
                if (this._card === source)
                    this._card = null;
            });
        } catch (error) {
            Main.notify('island-linux', 'Kartu gagal dibuka. Periksa path Python dan virtualenv, lalu pasang ulang extension.');
            console.error(`island-linux: ${error.message}`);
        }
    }

    disable() {
        this._alive = false;
        if (this._timer) {
            GLib.source_remove(this._timer);
            this._timer = 0;
        }
        this._cancellable?.cancel();
        this._inspect?.force_exit();
        this._inspect = null;
        this._card?.force_exit();
        this._card = null;
        // Kembalikan actor asli agar jam/kalender tidak hilang saat dinonaktifkan.
        if (this._clock && this._group) {
            this._group.remove_child(this._clock);
            const parent = this._group.get_parent() ?? this._parent;
            const index = parent.get_children().indexOf(this._group);
            parent.insert_child_at_index(this._clock, index >= 0 ? index : this._originalIndex);
        }
        this._group?.destroy();
        this._group = null;
        this._clock = null;
        this._parent = null;
        this._button = null;
        this._label = null;
        this._icon = null;
    }
}
