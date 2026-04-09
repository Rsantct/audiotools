#!/usr/bin/env python3
import  numpy               as np
import  matplotlib.pyplot   as plt
from    scipy               import signal, fftpack
from    scipy.io            import wavfile
import  argparse
import  os


def get_minimum_phase(h, n_fft):
    """Calcula la fase mínima a partir de la magnitud mediante Hilbert."""
    H = np.fft.fft(h, n_fft)
    mag = np.abs(H)
    mag = np.maximum(mag, 1e-12)
    log_mag = np.log(mag)
    min_phase = -fftpack.hilbert(log_mag).imag
    return min_phase


def smooth_curve(data, points_per_octave, N):
    if N is None or N <= 0: return data
    window_size = int(points_per_octave / N)
    if window_size < 3: return data
    window = np.hanning(window_size)
    window /= window.sum()
    return np.convolve(data, window, mode='same')


def load_filter(path, samplerate=None, bits='float32'):
    ext = os.path.splitext(path)[1].lower()
    if ext == '.wav':
        fs, data = wavfile.read(path)
        if len(data.shape) > 1: data = data[:, 0]
        if data.dtype == np.int16: data = data / 32768.0
        elif data.dtype == np.int32: data = data / 2147483648.0
    else:
        if samplerate is None: raise ValueError(f"Se requiere --fs para: {path}")
        dtype_map = {'int16': np.int16, 'float32': np.float32, 'float64': np.float64}
        data = np.fromfile(path, dtype=dtype_map[bits])
        if bits == 'int16': data = data / 32768.0
        fs = samplerate
    return data, fs


def format_freq_ticks(x, pos):
    if x >= 1000: return f'{int(x/1000)}K' if x % 1000 == 0 else f'{x/1000:.1f}K'
    return str(int(x))


def plot_filters(args):
    # --- Configuración de dimensiones y layout ---
    if args.only_mag:
        # Altura reducida (4.5) para un solo plot
        fig, ax_mag = plt.subplots(figsize=(9, 4.5), constrained_layout=True)
        ax_phase = None
        ax_gd = ax_imp = None
    else:
        # Altura completa (9) para tres plots
        fig, (ax_mag, ax_gd, ax_imp) = plt.subplots(
            3, 1, figsize=(9, 9), constrained_layout=True,
            gridspec_kw={'height_ratios': [2, 1, 1]}
        )
        ax_phase = ax_mag.twinx()

    colors = ['cornflowerblue', 'darkorange', 'forestgreen', 'maroon']
    ppo = 400

    for i, path in enumerate(args.files):

        h, fs = load_filter(path, args.fs, args.bits)

        f_ini = 1
        f_end = int(fs/2)
        f_log = np.logspace(np.log10(f_ini), np.log10(f_end), int(ppo * np.log2(f_end / f_ini)))

        w_log = 2 * np.pi * f_log / fs
        w, resp = signal.freqz(h, worN=w_log)
        mag_db = 20 * np.log10(np.abs(resp) + 1e-12)

        label_name = os.path.basename(path)
        ax_mag.semilogx(f_log, mag_db, color=colors[i], label=label_name, linewidth=1.5)

        # Si NO estamos en modo solo magnitud, procesamos Fase, GD e Impulso
        if not args.only_mag:
            total_phase_rad = np.angle(resp)
            if not args.no_excess:
                n_fft = max(16384, len(h) * 4)
                min_phase_full = get_minimum_phase(h, n_fft)
                freqs_fft = np.fft.fftfreq(n_fft, 1/fs)
                min_phase_interp = np.interp(f_log, freqs_fft[freqs_fft >= 0], min_phase_full[freqs_fft >= 0])
                display_phase = np.degrees(np.unwrap(total_phase_rad - min_phase_interp))
                phase_label = "Exceso de Fase (grados °)"
            else:
                display_phase = np.degrees(total_phase_rad)
                phase_label = "Fase Total (grados °)"

            ax_phase.semilogx(f_log, display_phase, color=colors[i], linestyle=':', alpha=0.5, linewidth=1)

            # Retardo de grupo
            _, gd = signal.group_delay((h, 1), w=w_log)
            gd_ms = (gd / fs) * 1000
            if args.gd_smooth: gd_ms = smooth_curve(gd_ms, ppo, args.gd_smooth)
            ax_gd.semilogx(f_log, np.where(mag_db > -60, gd_ms, np.nan), color=colors[i])

            # Impulso
            peak_idx = np.argmax(np.abs(h))
            ax_imp.plot(h, color=colors[i], alpha=0.8, label=f"{label_name} (Peak: {peak_idx} smp)")

    # --- Formateo de Coordenadas y Estética ---
    if args.only_mag:
        ax_mag.format_coord = lambda x, y: f"{int(x)} Hz    {y:.1f} dB"
    else:
        def report_combined_coord(x, y_phase):
            display_coord = ax_phase.transData.transform((x, y_phase))
            inv_mag = ax_mag.transData.inverted()
            _, y_mag = inv_mag.transform(display_coord)
            return f"{int(x)} Hz    {y_mag:.1f} dB    {int(y_phase)}°"

        ax_mag.format_coord = report_combined_coord
        ax_phase.format_coord = report_combined_coord
        ax_phase.set_ylabel(phase_label)
        if args.no_excess:
            ax_phase.set_ylim(-185, 185)
            ax_phase.set_yticks([-180, -90, 0, 90, 180])

    # Estética común Magnitud
    ax_mag.xaxis.set_major_formatter(plt.FuncFormatter(format_freq_ticks))
    ax_mag.set_xticks([20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000])
    ax_mag.set_xlim(args.Fini, args.Fend)
    ax_mag.grid(True, which='both', alpha=0.3)
    ax_mag.set_ylabel("Magnitud (dB)")
    ax_mag.set_ylim(args.dBmin, args.dBmax)
    ax_mag.set_yticks(np.arange(args.dBmin, args.dBmax + 1, 6))
    ax_mag.legend(loc='lower right', fontsize='small')

    if not args.only_mag:
        ax_gd.xaxis.set_major_formatter(plt.FuncFormatter(format_freq_ticks))
        ax_gd.set_xticks([20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000])
        ax_gd.set_xlim(args.Fini, args.Fend)
        ax_gd.grid(True, which='both', alpha=0.3)
        ax_gd.set_ylabel("GD (ms)")
        ax_gd.format_coord = lambda x, y: f"{int(x)} Hz    {y:.2f} ms"

        ax_imp.set_xlabel("Samples")
        ax_imp.legend(loc='upper right', fontsize='x-small')
        ax_imp.grid(True, alpha=0.3)
        ax_imp.format_coord = lambda x, y: f"smp: {int(x)}    Amp: {y:.4f}"

    plt.show()


def prepare_parser():
    parser.add_argument("files", nargs='+', help="Archivos de filtro")
    parser.add_argument("--fs", type=int, help="Samplerate para archivos raw")
    parser.add_argument("--bits", type=str, default='float32', choices=['int16', 'float32', 'float64'])
    parser.add_argument("--Fini", type=float, default=20, help='Frec inicial (20 Hz)')
    parser.add_argument("--Fend", type=float, default=20000, help='Frec inicial (20 KHz)')
    parser.add_argument("--dBmin", type=float, default=-42)
    parser.add_argument("--dBmax", type=float, default=12)
    parser.add_argument("--gd_smooth", type=int, help="Suavizado octava para GD")
    parser.add_argument("--no_excess", action='store_true', help="Muestra Fase Total")
    parser.add_argument("--only_mag", action='store_true', help="Solo gráfico de Magnitud dB")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Analizador FIR")
    prepare_parser()
    args = parser.parse_args()

    if len(args.files) > 4:
        print("Error: Máximo 4 archivos.")
    else:
        plot_filters(args)

