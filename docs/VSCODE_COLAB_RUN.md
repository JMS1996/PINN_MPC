# VS Code / Colab run guide

Open this repository folder in VS Code:

`C:\Users\jangm\Documents\New project\drive_upload_code\PINN_MPC`

## Which notebook to run

Run these notebooks in this order:

1. Training

   `notebooks/current/PINN/PINN_model_training_auto_v6_alpha_state.ipynb`

2. MPC / controller experiment

   `notebooks/current/mpc/PINN_MPC_v6_alpha_altitude_guidance_PID_RS_CEM_MPPI_debug_v5.ipynb`

There is also a load-only MPC notebook:

`notebooks/current/mpc/PINN_MPC_v6_alpha_LOAD_ONLY_PID_CEM_MPPI_v4_fast_debug_guidance.ipynb`

Use the load-only notebook when the trained model/checkpoint already exists and you only want to run the controller side.

## Recommended workflow

- Edit notebooks in VS Code.
- Let Google Drive for desktop sync this code folder to Drive.
- Keep training outputs, checkpoints, and large results in a separate Drive folder such as:

  `/MyDrive/Colab Results/PINN_MPC`

- Keep Google Drive for desktop in `Stream files` mode so Colab outputs do not automatically mirror back to this PC.

## Run with Colab from VS Code

Install these VS Code extensions:

- Python
- Jupyter
- Colab, publisher `google.colab`

Then:

1. Open this folder in VS Code:

   `C:\Users\jangm\Documents\New project\drive_upload_code\PINN_MPC`

2. Open the notebook you want to run.

3. Click `Select Kernel` in the top-right of the notebook.

4. Choose `Colab` > `Auto Connect` or `Colab` > `New Colab Server`.

5. Sign in to Google when prompted.

6. Use the command palette if you need Drive:

   `Colab: Mount Google Drive to Server...`

## Runtime paths

When a notebook runs on Colab, it runs on Google's server, not directly inside your Windows folder. Use Google Drive paths for anything the Colab runtime must read or write.

Recommended output folder:

`/content/drive/MyDrive/Colab Results/PINN_MPC`

Avoid writing large checkpoints, logs, or generated results inside this repository folder.
