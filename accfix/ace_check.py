# -*- coding: utf-8 -*-
import re
import shutil
from loguru import logger as log
from pathlib import Path
from subprocess import Popen, PIPE, STDOUT


ace_path = Path(shutil.which("ace"))
log.debug(f"Using ACE at {ace_path}")
ansi_escape = re.compile(r"\x1B[@-_][0-?]*[ -/]*[@-~]")


def ace_check(fp):
    # Run the ace command with subprocess.Popen
    fp = Path(fp)
    report_dir = fp.parent / f"{fp.stem}_report"
    report_dir.mkdir(exist_ok=True)

    # Run ACE Check
    cmd = [ace_path, "-f", "-o", report_dir, fp]
    process = Popen(cmd, stdout=PIPE, stderr=STDOUT, text=True)

    log_output = []
    for line in process.stdout:
        stripped_line = ansi_escape.sub("", line).strip()
        log.info(stripped_line)
        log_output.append(line)
        yield stripped_line

    process.wait()
    if process.returncode != 0:
        log_output.append(f"Ace command failed with return code {process.returncode}")
        yield f"Ace command failed with return code {process.returncode}"


if __name__ == "__main__":
    file = "../scratch/test1.epub"
    list(ace_check(file))
