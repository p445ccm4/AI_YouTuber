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
        topics_path = gr.Textbox(label="Enter topic file name: f\"inputs/{topics_basename}.topics\"", value="inputs/20250306.topics")
        with gr.Row():
            with gr.Column(): 
                load_topics_button = gr.Button("Load Topic File", variant="primary")
                topics_content = gr.Code(label="Topic File Content", language='shell', interactive=True, max_lines=30)
                save_topics_button = gr.Button("Save Topic File")

                load_topics_button.click(load_file_content, inputs=topics_path, outputs=topics_content)
                save_topics_button.click(save_file_content, inputs=[topics_path, topics_content], outputs=gr.Textbox(label="Last Update"))
            with gr.Column():
                print_status_button = gr.Button("Print Status", variant="primary")
                print_status_outputs = gr.Code(language='shell', interactive=True, max_lines=30)
                
                print_status_button.click(fn=ZZZ_print_status.print_status,inputs=topics_path, outputs=print_status_outputs)

        with gr.Tab("Browse and Edit Proposals"):
            def load_proposal_paths(topics_path, input_dir="inputs/proposals"):
                """Browses files in a directory and returns a list of filenames."""
                with open(topics_path, 'r') as f:
                    topics = [line.split()[0] for line in f.readlines() if line.strip() and not line.strip().startswith("#")]
                json_paths = [os.path.join(input_dir, f"{topic}.json") for topic in topics]
                return gr.Dropdown(choices=json_paths)

            proposal_path = gr.Dropdown(None, label="Proposal file path")
            proposal_content = gr.Code(label="Proposal Content",language="json", max_lines=20)
            save_proposal_button = gr.Button("Save Changes", variant="primary")
            
            load_topics_button.click(load_proposal_paths, inputs=topics_path, outputs=proposal_path)
            save_topics_button.click(load_proposal_paths, inputs=topics_path, outputs=proposal_path)
            proposal_path.change(load_file_content, inputs=proposal_path, outputs=proposal_content)
            save_proposal_button.click(save_file_content, inputs=[proposal_path, proposal_content], outputs=gr.Textbox(label="Last Update"))

        with gr.Tab("Create New Proposal"):
            new_proposal_path = gr.Textbox(label="New proposal file path")
            new_proposal_content = gr.Code(label="Proposal Content", language="json", max_lines=20)
            create_proposal_button = gr.Button("Create Proposal", variant="primary")

            create_proposal_button.click(save_file_content, inputs=[new_proposal_path, new_proposal_content], outputs=gr.Textbox(label="Last Update"))
        
        with gr.Tab("text2YTShorts_batch"):
            def interrupt(interrupt_flag_path):
                if os.path.exists(interrupt_flag_path):
                    os.remove(interrupt_flag_path)
                with open(interrupt_flag_path, "w") as f:
                    f.write("stop")
                gr.Warning("Process will stop after processing this video. Please wait...")

            def run_text2YTShorts_batch(topics_path, send_email, interrupt_flag_path): #, progress=gr.Progress(track_tqdm=True)): # have bug on nested tqdm
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

                for _ in text2YTShorts_batch.text2YTShorts_batch(topics_path, send_email, logger=logger):
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
                inputs=[topics_path, send_email_checkbox, interrupt_flag_path],
                outputs=text2YTShorts_batch_outputs,
                show_progress_on=text2YTShorts_batch_progress,
                show_progress="full",
                scroll_to_output=True
            )
            text2YTShorts_batch_stop_button.click(
                interrupt, inputs=interrupt_flag_path, outputs=None
            )

        with gr.Tab("Browse Videos (Local Machine Only)"):
            def load_topics(topics_path):
                with open(topics_path, 'r') as f:
                    topics = [line.split()[0] for line in f.readlines() if line.strip() and not line.strip().startswith("#")]
                return gr.Dropdown(value=None, choices=topics)
            
            def load_video_paths(topics_path, topic, output_dir="outputs"):
                prefix = os.path.basename(topics_path).split(".")[0]
                topic_dir = os.path.join(output_dir, f"{prefix}_{topic}")
                video_paths = []
                final_video_path = os.path.join(topic_dir, "final.mp4")
                if os.path.exists(final_video_path):
                    video_paths.append(final_video_path)
                for i in range(-1, 25):
                    sub_video_path = os.path.join(topic_dir, f"{i}_captioned.mp4")
                    if os.path.exists(sub_video_path):
                        video_paths.append(sub_video_path)
                return gr.Dropdown(value=None, choices=video_paths), video_paths
            
            def change_video_path(current_video_path, video_paths:list, mode):
                if current_video_path:
                    current_idx = video_paths.index(current_video_path)
                    offset = 1 if mode=="Next" else -1
                    current_idx = (current_idx + offset) % len(video_paths)
                    return video_paths[current_idx]
                else:
                    return video_paths[0]
            
            with gr.Row():
                topic = gr.Dropdown(None, label="Topic")
                video_path = gr.Dropdown(None, label="Video Path", scale=2)
                with gr.Column():
                    back_video_button = gr.Button("Back")
                    next_video_button = gr.Button("Next")
            video_player = gr.Video()
            video_paths = gr.State([])

            topic.change(fn=load_video_paths, inputs=[topics_path, topic], outputs=[video_path, video_paths])
            video_path.change(fn=lambda path: gr.Video(path, height="100vh"), inputs=video_path, outputs=video_player)
            load_topics_button.click(load_topics, inputs=topics_path, outputs=topic)
            save_topics_button.click(load_topics, inputs=topics_path, outputs=topic)
            next_video_button.click(change_video_path, inputs=[video_path, video_paths, next_video_button], outputs=video_path)
            back_video_button.click(change_video_path, inputs=[video_path, video_paths, back_video_button], outputs=video_path)
            
        with gr.Tab("Upload to YouTube (Local Machine Only)"):
            def run_upload(topics, publish_date, video_per_day, progress=gr.Progress(track_tqdm=True)):
                logger = logging.getLogger(__name__)
                logger.setLevel(logging.DEBUG)
                formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
                string_stream = io.StringIO()
                string_handler = logging.StreamHandler(string_stream)
                string_handler.setFormatter(formatter)
                logger.addHandler(string_handler)

                uploader = upload_YouTube.YouTubeUploader(logger=logger)
                for _ in uploader.upload_from_topic_file(topics, publish_date, int(video_per_day)):
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
                inputs=[topics_path, publish_date, video_per_day],
                outputs=upload_outputs,
                show_progress="full",
                show_progress_on=upload_progress,
                scroll_to_output=True
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