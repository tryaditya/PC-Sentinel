
import subprocess
import winreg


def get_cpu_name():
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
        )
        with key:
            name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
        return name.strip()
    except (OSError, FileNotFoundError):
        return "CPU name unavailable"



def get_ram_speed():
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "(Get-CimInstance Win32_PhysicalMemory | "
                "Select-Object -ExpandProperty ConfiguredClockSpeed)",
            ],
            capture_output=True,
            text=True,
            timeout=8,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        if result.returncode == 0:
            speeds = [
                int(line.strip())
                for line in result.stdout.splitlines()
                if line.strip().isdigit() and int(line.strip()) > 0
            ]

            if speeds:
                return f"{min(speeds)} MHz"

    except (OSError, subprocess.TimeoutExpired, ValueError):
        pass

        return "Unavailable"


        speed = result.stdout.strip()

        if result.returncode == 0 and speed.isdigit():
            return f"{speed} MHz"

    except (OSError, subprocess.TimeoutExpired):
        pass

    return "Unavailable"


def get_gpu_info():
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.used,memory.total,"
                "utilization.gpu,temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        if result.returncode != 0:
            return None

        values = [value.strip() for value in result.stdout.splitlines()[0].split(",")]

        if len(values) != 5:
            return None

        name, used, total, utilization, temperature = values

        return {
            "name": name,
            "memory_used": float(used) if used.replace(".", "", 1).isdigit() else None,
            "memory_total": float(total) if total.replace(".", "", 1).isdigit() else None,
            "utilization": float(utilization) if utilization.replace(".", "", 1).isdigit() else None,
            "temperature": float(temperature) if temperature.replace(".", "", 1).isdigit() and float(temperature) > 0 else None,
        }

    except (OSError, subprocess.TimeoutExpired, IndexError, ValueError):
        return None
