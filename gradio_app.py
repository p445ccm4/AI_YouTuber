import os
import gradio as gr
import time
import logging
import io
import datetime

# --- Import Functions Directly ---
import ZZZ_print_status
import ZZZ_print_titles
import text2YTShorts_batch
import upload_YouTube

def load_file_content(path):
    if os.path.exists(path):
        with open(path, 'r') as f:
            content = f.read()
        return content
    return ""

def save_file_content(path, content):
    with open(path, 'w') as f:
        f.write(content)
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

# --- Gradio Interface ---
def create_demo():
    with gr.Blocks() as demo:
        with gr.Column(): # Stays at the top
            topic_file_path = gr.Textbox(label="Enter topic file name: f\"inputs/{topic_file_basename}.topics\"", value="inputs/20250306.topics")
            load_topic_file_button = gr.Button("Load Topic File")
            topic_file_content = gr.Code(label="Topic File Content", language='shell', interactive=True, max_lines=30)
            save_topic_file_button = gr.Button("Save Topic File")

            load_topic_file_button.click(load_file_content, inputs=topic_file_path, outputs=topic_file_content)
            save_topic_file_button.click(save_file_content, inputs=[topic_file_path, topic_file_content], outputs=gr.Textbox(label="Last Update"))

        with gr.Tab("Browse and Edit Proposals"):
            def load_proposal_file_paths(topic_file_path, input_dir="inputs/proposals"):
                """Browses files in a directory and returns a list of filenames."""
                with open(topic_file_path, 'r') as f:
                    topics = [line.split()[0] for line in f.readlines() if line.strip() and not line.strip().startswith("#")]
                json_files = [os.path.join(input_dir, f"{topic}.json") for topic in topics]
                return gr.Dropdown(choices=json_files)

            with gr.Row():
                proposal_file_path = gr.Dropdown(None, label="Proposal file path")
            with gr.Row():
                proposal_content = gr.Code(label="Proposal Content",language="json", max_lines=20)
            with gr.Row():
                save_proposal_file_button = gr.Button("Save Changes")
            
            load_topic_file_button.click(load_proposal_file_paths, inputs=topic_file_path, outputs=proposal_file_path)
            save_topic_file_button.click(load_proposal_file_paths, inputs=topic_file_path, outputs=proposal_file_path)
            proposal_file_path.change(load_file_content, inputs=proposal_file_path, outputs=proposal_content)
            save_proposal_file_button.click(save_file_content, inputs=[proposal_file_path, proposal_content], outputs=gr.Textbox(label="Last Update"))

        with gr.Tab("Create New Proposal"):
            with gr.Row():
                new_proposal_file_path = gr.Textbox(label="New proposal file path")
            with gr.Row():
                new_proposal_content = gr.Code(label="Proposal Content", language="json", max_lines=20)
            with gr.Row():
                create_proposal_button = gr.Button("Create Proposal")

            create_proposal_button.click(save_file_content, inputs=[new_proposal_file_path, new_proposal_content], outputs=gr.Textbox(label="Last Update"))
        
        with gr.Tab("text2YTShorts_batch"):
            def interrupt(interrupt_flag_path):
                if os.path.exists(interrupt_flag_path):
                    os.remove(interrupt_flag_path)
                with open(interrupt_flag_path, "w") as f:
                    f.write("stop")
                gr.Warning("Process will stop after processing this video. Please wait...")

            def run_text2YTShorts_batch(topic_file_path, send_email, interrupt_flag_path, progress=gr.Progress(track_tqdm=True)):
                if interrupt_flag_path:
                    if os.path.exists(interrupt_flag_path):
                        os.remove(interrupt_flag_path)
                    with open(interrupt_flag_path, "w") as f:
                        f.write("running")
                logger = logging.getLogger(__name__)
                logger.setLevel(logging.DEBUG)
                formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
                string_stream = io.StringIO()
                string_handler = logging.StreamHandler(string_stream)
                string_handler.setFormatter(formatter)
                logger.addHandler(string_handler)

                for _ in text2YTShorts_batch.text2YTShorts_batch(topic_file_path, send_email, logger=logger):
                    with open(interrupt_flag_path, "r") as f:
                        flag = f.readline().strip()
                    yield string_stream.getvalue()
                    if flag == "stop":
                        logger.error("Process Interrupted")
                        break
                yield string_stream.getvalue()
            
            with gr.Row():
                send_email_checkbox = gr.Checkbox(label="Send Email", value=False)
                text2YTShorts_batch_generate_button = gr.Button("Generate", variant="primary")
                text2YTShorts_batch_stop_button = gr.Button("Stop", variant="stop")
                interrupt_flag_path = gr.Text(".gradio/interrupt_flag", visible=False)
            text2YTShorts_batch_progress = gr.Textbox(label="Progress Bar")
            text2YTShorts_batch_outputs = gr.Textbox(label="Output", lines=30, max_lines=30)
            text2YTShorts_batch_generate_button.click(
                fn=run_text2YTShorts_batch,
                inputs=[topic_file_path, send_email_checkbox, interrupt_flag_path],
                outputs=text2YTShorts_batch_outputs,
                show_progress_on=text2YTShorts_batch_progress,
                show_progress="full"
            )
            text2YTShorts_batch_stop_button.click(
                interrupt, inputs=interrupt_flag_path, outputs=None
            )
            
        with gr.Tab("Upload to YouTube (Local Machine Only)"):
            def run_upload(topic_file_path, publish_date, video_per_day, progress=gr.Progress(track_tqdm=True)):
                logger = logging.getLogger(__name__)
                logger.setLevel(logging.DEBUG)
                formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
                string_stream = io.StringIO()
                string_handler = logging.StreamHandler(string_stream)
                string_handler.setFormatter(formatter)
                logger.addHandler(string_handler)

                uploader = upload_YouTube.YouTubeUploader(logger=logger)
                for _ in uploader.upload_from_topic_file(topic_file_path, publish_date, int(video_per_day)):
                    yield string_stream.getvalue()
                yield string_stream.getvalue()

            with gr.Row():
                publish_date = gr.Textbox(datetime.date.today().strftime('%Y-%m-%d'), label="Publish Date (YYYY-MM-DD)")
                video_per_day = gr.Textbox("3", label="Video per day")
                upload_button = gr.Button("Upload Videos", variant="primary")
            upload_progress = gr.Textbox(label="Progress Bar")
            upload_outputs = gr.Textbox(label="Output", lines=30, max_lines=30)
            upload_button.click(
                fn=run_upload,
                inputs=[topic_file_path, publish_date, video_per_day],
                outputs=upload_outputs,
                show_progress="full",
                show_progress_on=upload_progress
            )

        with gr.Tab("Print Status"):
            gr.Interface(
                fn=ZZZ_print_status.print_status,
                inputs=topic_file_path,
                outputs=gr.Code(label="Output", language='shell', interactive=True),
                title="print_status",
                flagging_mode="never",
                submit_btn="Print",
            )

        with gr.Tab("Print Titles"):
            gr.Interface(
                fn=ZZZ_print_titles.print_titles,
                inputs=gr.Textbox("inputs/proposals", label="Folder Path"),
                outputs=gr.Code(label="Output", language='markdown', interactive=True),
                title="print_titles",
                flagging_mode="never",
                submit_btn="Print",
            )

    return demo

if __name__ == "__main__":
    demo = create_demo()
    demo.launch(share=True)