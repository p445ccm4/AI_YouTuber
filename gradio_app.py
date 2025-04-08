import os
import gradio as gr
import time
import logging
import io
import datetime
import gradio_client

# --- Import Functions Directly ---
import ZZZ_print_status
import ZZZ_print_titles
import text2YTShorts_batch
import upload_YouTube
import llm
import transcript_YouTube

# --- Set up loggers for text-to-YTShorts and YTuploader ---
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

text2YTShorts_logger = logging.getLogger("text-to-YTShorts")
text2YTShorts_logger.setLevel(logging.DEBUG)
text2YTShorts_string_stream = io.StringIO()
text2YTShorts_string_handler = logging.StreamHandler(text2YTShorts_string_stream)
text2YTShorts_string_handler.setFormatter(formatter)
text2YTShorts_logger.addHandler(text2YTShorts_string_handler)

YTUploader_logger = logging.getLogger("YTUploader")
YTUploader_logger.setLevel(logging.DEBUG)
YTUploader_string_stream = io.StringIO()
YTUploader_string_handler = logging.StreamHandler(YTUploader_string_stream)
YTUploader_string_handler.setFormatter(formatter)
YTUploader_logger.addHandler(YTUploader_string_handler)

def load_file_content(path):
    with open(path, 'r') as f:
        content = f.read()
    return content

def save_file_content(path, content):
    with open(path, 'w') as f:
        f.write(content)
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def load_topic_paths(input_dir="inputs"):
    return sorted([os.path.join(input_dir, filename) for filename in os.listdir(input_dir) if filename.endswith(".topics")], reverse=True)
           
def load_proposal_paths(topics_path, input_dir="inputs/proposals"):
    """Browses files in a directory and returns a list of filenames."""
    with open(topics_path, 'r') as f:
        topics = [line.split()[0] for line in f.readlines() if line.strip() and not line.strip().startswith("#")]
    json_paths = [os.path.join(input_dir, f"{topic}.json") for topic in topics]
    return gr.Dropdown(value=json_paths[0], choices=json_paths)

def load_topics(topics_path):
    with open(topics_path, 'r') as f:
        topics = [line.split()[0] for line in f.readlines() if line.strip() and not line.strip().startswith("#")]
    return gr.Dropdown(value=topics[0], choices=topics), topics

# --- Gradio Interface ---
def create_demo():
    with gr.Blocks(title="AI YTB") as demo:
        with gr.Row():
            topics_path = gr.Dropdown(label="Topic file name", choices=load_topic_paths(),  allow_custom_value=True)
        with gr.Row():
            with gr.Column(): 
                # load_topics_button = gr.Button("Load Topic File", variant="primary")
                topics_content = gr.Code(value=load_file_content, inputs=topics_path, label="Topic File Content", language='shell', interactive=True, max_lines=30)
                save_topics_button = gr.Button("Save Topic File", variant="primary")
                save_topics_outputs = gr.Textbox(label="Last Update")

            with gr.Column():
                print_status_button = gr.Button("Print Status", variant="primary")
                print_status_outputs = gr.Code(label="Current Status", language='shell', interactive=True, max_lines=30)
                apply_status_button = gr.Button("Copy to left", variant="primary")
                
            apply_status_button.click(fn=lambda x: x, inputs=print_status_outputs, outputs=topics_content)
            print_status_button.click(fn=ZZZ_print_status.print_status,inputs=topics_path, outputs=print_status_outputs)
            save_topics_button.click(
                save_file_content, inputs=[topics_path, topics_content], outputs=save_topics_outputs
            )


        with gr.Tab("Transcript from Existing YouTube Videos"):
            video_urls = gr.Code(label="Video URLs and Shorts per Video", language="shell", max_lines=30)
            series = gr.Dropdown(["Relationship", "Motivation", "MBTI", "Zodiac", "Other"], label="Series")
            topics_path
            transcribe_and_make_button = gr.Button("Transribe and Make Videos", variant="primary")
            transcribe_and_make_outputs = gr.Textbox(label="Progress Output", max_lines=30)

            transcribe_and_make_button.click(fn=transcript_YouTube.make_proposals, inputs=[video_urls, series, topics_path], outputs=transcribe_and_make_outputs)

        with gr.Tab("Create or Edit Proposals"):
            def ask_LLM(proposal_content, modified_proposal_content, user_input):
                proposal_content = modified_proposal_content or proposal_content
                with open("inputs/System_Prompt_Proposal.txt", "r") as f:
                    system_prompt = f.read()
                message = "\n\n".join([user_input, proposal_content])
                response = llm.gen_response(message, [], "deepseek-v3", system_prompt)
                yield from response
            with gr.Row():
                with gr.Column():
                    proposal_path = gr.Dropdown(value=load_proposal_paths, inputs=topics_path, label="Proposal file path")
                    proposal_content = gr.Code(load_file_content, inputs=proposal_path, label="Proposal Content",language="json", max_lines=20)
                    save_proposal_button = gr.Button("Save Proposal", variant="primary")
                with gr.Column():
                    LLM_user_input = gr.Textbox(label="Ask LLM to modify the proposal")
                    modified_proposal_content = gr.Code(None, label="Modified Proposal Content", language="json", max_lines=20)
                    ask_llm_button = gr.Button("Ask LLM", variant="primary")
                    apply_llm_button = gr.Button("Copy to left", variant="primary")
            
            ask_llm_button.click(fn=ask_LLM, inputs=[proposal_content, modified_proposal_content, LLM_user_input], outputs=modified_proposal_content)
            apply_llm_button.click(fn=lambda x: x, inputs=modified_proposal_content, outputs=proposal_content)
            save_proposal_button.click(save_file_content, inputs=[proposal_path, proposal_content], outputs=gr.Textbox(label="Last Update"))
        
        with gr.Tab("Process Text-to-YTShorts Batch"):
            def interrupt(interrupt_flag_path):
                if os.path.exists(interrupt_flag_path):
                    os.remove(interrupt_flag_path)
                with open(interrupt_flag_path, "w") as f:
                    f.write("stop")
                gr.Warning("Process will stop after processing this video. Please wait...")

            def run_text2YTShorts_batch(topics_path, send_email, interrupt_flag_path, progress=gr.Progress(track_tqdm=True)): # have bug on nested tqdm
                if interrupt_flag_path:
                    if os.path.exists(interrupt_flag_path):
                        os.remove(interrupt_flag_path)
                    with open(interrupt_flag_path, "w") as f:
                        f.write("running")
                text2YTShorts_string_stream.truncate(0)
                text2YTShorts_string_stream.seek(0)

                for _ in text2YTShorts_batch.text2YTShorts_batch(topics_path, send_email, logger=text2YTShorts_logger):
                    with open(interrupt_flag_path, "r") as f:
                        flag = f.readline().strip()
                    yield text2YTShorts_string_stream.getvalue()
                    if flag == "stop":
                        text2YTShorts_logger.error("Process Interrupted")
                        raise GeneratorExit()
                return text2YTShorts_string_stream.getvalue() + "Process Ended"
            
            with gr.Row():
                send_email_checkbox = gr.Checkbox(label="Send Email", value=False)
                text2YTShorts_batch_generate_button = gr.Button("Generate", variant="primary")
                text2YTShorts_batch_stop_button = gr.Button("Stop", variant="stop")
                interrupt_flag_path = gr.Text(".gradio/interrupt_flag", visible=False)
            text2YTShorts_batch_progress = gr.Textbox(label="Progress Bar")
            text2YTShorts_batch_outputs = gr.Textbox(text2YTShorts_string_stream.getvalue, label="Output", lines=30, max_lines=30)
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

        with gr.Tab("Browse Videos"):
            def next_choice(current_choice, all_choices:list):
                if current_choice:
                    current_idx = all_choices.index(current_choice)
                    current_idx = (current_idx + 1) % len(all_choices)
                    return all_choices[current_idx]
                else:
                    return all_choices[0]
                

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
                return gr.Dropdown(value=video_paths[0], choices=video_paths), video_paths

            with gr.Row():
                current_topic = gr.Dropdown(None, label="Topic")
                current_video_path = gr.Dropdown(None, label="Video Path", scale=2)
                with gr.Column():
                    next_topic_button = gr.Button("Next Topic")
                    next_video_button = gr.Button("Next Video")
            video_player = gr.Video()
            video_paths = gr.State([])
            topics = gr.State([])

            demo.load(
                load_topics, inputs=topics_path, outputs=[current_topic, topics]
            ).then(
                fn=load_video_paths, inputs=[topics_path, current_topic], outputs=[current_video_path, video_paths]
            ).then(
                fn=lambda path: gr.Video(path, height="100vh"), inputs=current_video_path, outputs=video_player
            )
            topics_path.change(
                load_topics, inputs=topics_path, outputs=[current_topic, topics]
            )
            current_topic.change(fn=load_video_paths, inputs=[topics_path, current_topic], outputs=[current_video_path, video_paths])
            current_video_path.change(fn=lambda path: gr.Video(path, height="100vh"), inputs=current_video_path, outputs=video_player)
            next_video_button.click(next_choice, inputs=[current_video_path, video_paths], outputs=current_video_path)
            next_topic_button.click(next_choice, inputs=[current_topic, topics], outputs=current_topic)
            
        with gr.Tab("Upload to YouTube (Local Machine Only)"):
            def run_upload(topics, publish_date, video_per_day, progress=gr.Progress(track_tqdm=True)):
                YTUploader_string_stream.truncate(0)
                YTUploader_string_stream.seek(0)
                
                uploader = upload_YouTube.YouTubeUploader(logger=YTUploader_logger)
                for _ in uploader.upload_from_topic_file(topics, publish_date, int(video_per_day)):
                    yield YTUploader_string_stream.getvalue()
                yield YTUploader_string_stream.getvalue()

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
    demo.launch(
        server_name="0.0.0.0",
        server_port=1388,
        # share=True,
        )