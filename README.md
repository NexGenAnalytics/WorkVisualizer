
<img src="app/workvisualizer/public/wv_readme_wordmark.png">

---

The **WorkVisualizer** is an interactive, high-level performance analysis tool from NexGen Analytics designed to facilitate profiling of scientific applications.

Jump to:
- [Overview](#overview)
- [Contents](#contents)
- [Generating Data](#generating-data)
- [App](#app)
  - [Set-Up](#set-up)
  - [Opening the App](#opening-the-app)
  - [Using the App](#using-the-app)
  - [Caveats](#caveats)
- [Credits](#credits)

---

## Overview

The WorkVisualizer is a locally hosted web app that offers quick, actionable insights for a user's Kokkos-based application by highlighting areas in the code where time is being lost.
"Lost time" refers to moments in the program's runtime during which most ranks are waiting for other ranks to execute a task.

If you encounter any issues with the WorkVisualizer, please open an issue.

## Contents

Currently, this repository contains the following directories and files:

1. `caliper.config`: The configuration file that will be used to generate the data prior to analysis and visualization. Instructions for use are included below.

2. `app/workvisualizer/`: The core WorkVisualizer web app

3. `scripts/`: Helper scripts for repository management

3. `mockups/`: Sample mock-ups for the end result of the Work Visualizer

4. `data/`: Sample data from running [ExaMiniMD](https://github.com/ECP-copa/ExaMiniMD)

5. `misc/`: Artifacts of development (scripts, plots, and old JSON)

## Generating Data

These instructions explain how to generate a data dump for any given application.

The steps assume that the top-level of the Work Visualizer repository has been exported to `$WORKVIZ_DIR`.

1. Install [Caliper](https://github.com/LLNL/Caliper) with the following configuration (where `${CALIPER_SOURCE_DIR}` and `${CALIPER_INSTALL_DIR}` must be either exported beforehand or filled in manually):
```cmake
cmake -D BUILD_TESTING=Off \
      -D WITH_MPI=On \
      -D WITH_TOOLS=Off \
      -D CMAKE_BUILD_TYPE=Debug \
      -D CMAKE_INSTALL_PREFIX="${CALIPER_INSTALL_DIR}"\
      "${CALIPER_SOURCE_DIR}"
```

_Note: At least for the moment, Caliper must be installed in Debug mode._


2. Export the following environment variables:

```sh
export KOKKOS_TOOLS_LIBS=/path/to/libcaliper.so
export CALI_CONFIG_FILE=${WORKVIZ_DIR}/caliper.config
```

3. Run an executable that uses Kokkos
   - This will automatically generate `data-<mpi.rank>.cali` files in the directory where you ran the executable (one file per rank).

## App

These instructions explain how to get the WorkVisualizer web app running locally.

### Set-Up

If it is your first time using the WorkVisualizer, follow these steps to prepare your environment.

1. Install Node.js
```sh
sudo apt update
sudo apt install nodejs
```

2. Install Node Version Manager (`nvm`)
```sh
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.38.0/install.sh | bash
# Close and reopen terminal, or run:
source ~/.bashrc
```

3. Install Node.js verison >= 20
```sh
nvm install 20
nvm use 20
```

4. Install necessary Python packages
```sh
pip install -r ${WORKVIZ_DIR}/app/workvisualizer/requirements.txt
```

5. From the `${WORKVIZ_DIR}/app/workvisualizer` directory, run:
```sh
npm install
```

### Opening the App

Once your environment is prepared, open two terminal instances.

1. In one terminal instance, run
```sh
cd ${WORKVIZ_DIR}/app/workvisualizer/api
uvicorn main:app --reload
```

2. In a separate terminal, run

```sh
cd ${WORKVIZ_DIR}/app/workvisualizer
npm run dev
```

You will see something like:

```
> workvisualizer@0.1.0 dev
> next dev

  ▲ Next.js 14.2.3
  - Local:        http://localhost:3000

 ✓ Starting...
 ✓ Ready in 1983ms
```

The WorkVisualizer is available at the provided local address (in this case, `http://localhost:3000`).

Copy/paste this into your browser to access the app.

### Using the App

1. Click `Upload File(s)` and select any `.cali` files you would like to see analyzed (see Generating Data section above).
    - There are sample `.cali` files in `data/cali` (generated by running ExaMiniMD on 4 ranks for 100 timesteps)

2. Explore the WorkVisualizer, using the `?` buttons for guidance.

### Caveats

Version 1.0.0-alpha of the WorkVisualizer is a prototype intended as a simple proof of concept.

Currently, the WorkVisualizer requires that an application meet the following criteria:
1. Uses the [Kokkos](https://kokkos.org/) programming model
2. Features MPI collective calls

Additionally, while the WorkVisualizer has been tested to work on up to 1024 ranks, latency becomes apparent as the number of ranks surpasses 100. Future work will greatly improve the scalability. For now, consider testing your code with smaller runs (both shorter durations and fewer ranks).

## Credits

The WorkVisualizer 1.0.0-alpha was supported by the U.S. Department of Energy, Office of Science, Office of Advanced Scientific Computing Research through the Small Business Innovation Research (SBIR) Program, under SBIR Phase I Award DE-SC-0024832.
