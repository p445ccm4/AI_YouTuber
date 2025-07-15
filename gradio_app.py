import os
import gradio as gr
import time
import logging
import io
import datetime

# --- Import Functions Directly ---
import ZZZ_print_status
import ZZZ_print_titles
import text2YTVideos_batch
import upload_YouTube
import llm
import yt_url_to_proposals

# --- Set up loggers for text-to-YTShorts and YTuploader ---
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

text2YTVideos_logger = logging.getLogger("text-to-YTVideos")
text2YTVideos_logger.setLevel(logging.DEBUG)
text2YTVideos_string_stream = io.StringIO()
text2YTVideos_string_handler = logging.StreamHandler(text2YTVideos_string_stream)
text2YTVideos_string_handler.setFormatter(formatter)
text2YTVideos_logger.addHandler(text2YTVideos_string_handler)

YTUploader_logger = logging.getLogger("YTUploader")
YTUploader_logger.setLevel(logging.DEBUG)
YTUploader_string_stream = io.StringIO()
YTUploader_string_handler = logging.StreamHandler(YTUploader_string_stream)
YTUploader_string_handler.setFormatter(formatter)
YTUploader_logger.addHandler(YTUploader_string_handler)

def load_file_content(path):
    if not path or not os.path.exists(path):
        return ""
    with open(path, 'r') as f:
        content = f.read()
    return content

def save_file_content(path, content):
    with open(path, 'w') as f:
        f.write(content)
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def load_topics_file_paths(input_dir="inputs"):
    topics_file_paths = sorted([os.path.join(input_dir, filename) for filename in os.listdir(input_dir) if filename.endswith(".topics")], reverse=True)
    return gr.Dropdown(choices=topics_file_paths, value=topics_file_paths[0])
           
def load_proposal_paths(topics_file_path, input_dir="inputs/proposals"):
    if not topics_file_path or not os.path.exists(topics_file_path):
        return gr.Dropdown(None)
    with open(topics_file_path, 'r') as f:
        topics = [line.split()[0] for line in f.readlines() if line.strip() and not line.strip().startswith("#")]
    json_paths = [os.path.join(input_dir, f"{topic}.json") for topic in topics]
    return gr.Dropdown(choices=json_paths, value=json_paths[0])

def load_topics(topics_file_path):
    if not os.path.exists(topics_file_path):
        return gr.Dropdown(None), []
    with open(topics_file_path, 'r') as f:
        topics = [line.split()[0] for line in f.readlines() if line.strip() and not line.strip().startswith("#")]
    return gr.Dropdown(choices=topics, value=topics[0]), topics

# --- Gradio Interface ---
def create_demo():
    with gr.Blocks(title="AI YTB") as demo:
        with gr.Row():
            topics_file_path = gr.Dropdown(label="Topic file name", allow_custom_value=True)
        with gr.Row():
            with gr.Column(): 
                topics_content = gr.Code(value=load_file_content, inputs=topics_file_path, label="Topic File Content", language='shell', interactive=True, max_lines=30)
                save_topics_button = gr.Button("Save Topic File", variant="primary")
                save_topics_outputs = gr.Textbox(label="Last Update")

            with gr.Column():
                print_status_outputs = gr.Code(label="Current Status", language='shell', interactive=True, max_lines=30)
                print_status_button = gr.Button("Print Status", variant="primary")
                apply_status_button = gr.Button("Copy to left", variant="huggingface")
                
            apply_status_button.click(
                fn=lambda x: x, inputs=print_status_outputs, outputs=topics_content
            ).success(
                save_file_content, inputs=[topics_file_path, topics_content], outputs=save_topics_outputs
            )
            print_status_button.click(fn=ZZZ_print_status.print_status,inputs=topics_file_path, outputs=print_status_outputs)
            save_topics_button.click(
                save_file_content, inputs=[topics_file_path, topics_content], outputs=save_topics_outputs
            )

        with gr.Tab("Make Proposals from Existing YouTube Videos"):
            with gr.Row():
                yt_urls_and_series = gr.Code(label="Video URLs and series", language="shell", max_lines=30)
                with gr.Column():
                    new_topics_file_path = gr.Dropdown(label="Topics file name", allow_custom_value=True)
                    # series = gr.Dropdown(["Relationship", "Motivation", "MBTI", "Zodiac", "Other"], label="Series", allow_custom_value=True)
                    # start_index = gr.Textbox("1", label="Start Index")
                    ollama_model_transcribe = gr.Dropdown(label="ollama model", choices=llm.get_ollama_model_names(), value="qwen3:32b")
            make_proposals_only_button = gr.Button("Make Proposals", variant="primary")
            make_proposals_and_generate_videos_button = gr.Button("Make Proposals and Videos (Experimental)", variant="huggingface")
            make_proposals_outputs = gr.Textbox(label="Progress Output", max_lines=30)

            make_proposals_only_button.click(fn=yt_url_to_proposals.transcribe_and_make_proposals, inputs=[yt_urls_and_series, new_topics_file_path, ollama_model_transcribe], outputs=make_proposals_outputs)

            # TODO: add a new section underneath after generating topics file.
            # Allow user to give follow-up ammendments for the proposal

        with gr.Tab("Create or Edit Proposals"):
            def ask_LLM(proposal_content, modified_proposal_content, user_input, ollama_model):
                proposal_content = modified_proposal_content or proposal_content
                with open("inputs/System_Prompt_Proposal_Single.txt", "r") as f:
                    system_prompt = f.read()
                message = "\n\n".join([user_input, proposal_content])
                for response in llm.gen_response(message, [], ollama_model, system_prompt):
                    yield response
                _, _, response = response.rpartition("/<think>")

            with gr.Row():
                with gr.Column():
                    proposal_path = gr.Dropdown(value=load_proposal_paths, inputs=topics_file_path, label="Proposal file path")
                    proposal_content = gr.Code(load_file_content, inputs=proposal_path, label="Proposal Content",language="json", max_lines=20)
                    save_proposal_button = gr.Button("Save Proposal", variant="primary")
                with gr.Column():
                    with gr.Row():
                        LLM_user_input = gr.Textbox(label="Ask LLM to modify the proposal", submit_btn=True)
                        ollama_model_edit_proposal = gr.Dropdown(label="ollama model", choices=llm.get_ollama_model_names(), value="qwen3:32b")
                        # ask_llm_button = gr.Button("Ask LLM", variant="primary")
                    modified_proposal_content = gr.Code(None, label="Modified Proposal Content", language="json", max_lines=20)
                    apply_llm_button = gr.Button("Copy to left", variant="primary")
            
            LLM_user_input.submit(fn=ask_LLM, inputs=[proposal_content, modified_proposal_content, LLM_user_input, ollama_model_edit_proposal], outputs=modified_proposal_content)
            apply_llm_button.click(fn=lambda x: x, inputs=modified_proposal_content, outputs=proposal_content)
            save_proposal_button.click(save_file_content, inputs=[proposal_path, proposal_content], outputs=gr.Textbox(label="Last Update"))
        
        with gr.Tab("Process Text-to-YTVideos Batch", id="Process Text-to-YTVideos Batch"):
            def interrupt(interrupt_flag_path):
                if os.path.exists(interrupt_flag_path):
                    os.remove(interrupt_flag_path)
                with open(interrupt_flag_path, "w") as f:
                    f.write("stop")
                gr.Warning("Process will stop after processing this video. Please wait...")

            def run_text2YTVideos_batch(topics_path, send_email, make_shorts, ollama_model, interrupt_flag_path, progress=gr.Progress(track_tqdm=True)):
                if interrupt_flag_path:
                    if os.path.exists(interrupt_flag_path):
                        os.remove(interrupt_flag_path)
                    with open(interrupt_flag_path, "w") as f:
                        f.write("running")
                text2YTVideos_string_stream.truncate(0)
                text2YTVideos_string_stream.seek(0)

                for _ in text2YTVideos_batch.text2YTVideos_batch(topics_path, send_email, make_shorts, logger=text2YTVideos_logger, ollama_model=ollama_model):
                    with open(interrupt_flag_path, "r") as f:
                        flag = f.readline().strip()
                    yield text2YTVideos_string_stream.getvalue()

                    if flag == "stop":
                        text2YTVideos_logger.error("Process Interrupted")
                        yield text2YTVideos_string_stream.getvalue()
                        break
                
                end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                text2YTVideos_logger.info(f"Process Ended at {end_time}")
                gr.Success(f"Process Ended at {end_time}", duration=0)
                yield text2YTVideos_string_stream.getvalue()
            
            with gr.Row():
                send_email_checkbox = gr.Checkbox(label="Send Email", value=False)
                make_shorts_checkbox = gr.Checkbox(label="Make Shorts", value=False)
                ollama_model_text2YTVideos = gr.Dropdown(label="ollama model", choices=llm.get_ollama_model_names(), value="qwen3:32b")
                with gr.Column():
                    text2YTVideos_batch_generate_button = gr.Button("Generate", variant="primary")
                    text2YTVideos_batch_stop_button = gr.Button("Stop", variant="stop")
            interrupt_flag_path = gr.Text(".gradio/interrupt_flag", visible=False)
            text2YTVideos_batch_progress = gr.Textbox(label="Progress Bar")
            text2YTVideos_batch_outputs = gr.Textbox(text2YTVideos_string_stream.getvalue, label="Output", lines=30, max_lines=30)
            text2YTVideos_batch_generate_button.click(
                fn=run_text2YTVideos_batch,
                inputs=[topics_file_path, send_email_checkbox, make_shorts_checkbox, ollama_model_text2YTVideos, interrupt_flag_path],
                outputs=text2YTVideos_batch_outputs,
                show_progress_on=text2YTVideos_batch_progress,
                show_progress="full",
                scroll_to_output=True
            )
            text2YTVideos_batch_stop_button.click(
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
                for filename in os.listdir(topic_dir):
                    if not filename.endswith("_captioned.mp4"):
                        continue
                    sub_video_path = os.path.join(topic_dir, filename)
                    video_paths.append(sub_video_path)
                video_paths.sort(key=lambda path: int(os.path.basename(path).removesuffix("_captioned.mp4")))
                
                final_video_path = os.path.join(topic_dir, "final.mp4")
                if os.path.exists(final_video_path):
                    video_paths.insert(0, final_video_path)
                
                first_value = video_paths[0] if video_paths else None
                return gr.Dropdown(choices=video_paths, value=first_value), video_paths

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
                load_topics_file_paths, outputs=topics_file_path
            ).then(
                load_topics_file_paths, outputs=new_topics_file_path
            ).then(
                load_topics, inputs=topics_file_path, outputs=[current_topic, topics]
            ).then(
                fn=load_video_paths, inputs=[topics_file_path, current_topic], outputs=[current_video_path, video_paths]
            ).then(
                fn=lambda path: gr.Video(path, height="80vh"), inputs=current_video_path, outputs=video_player
            )
            topics_file_path.change(
                load_file_content, inputs=topics_file_path, outputs=topics_content
            ).then(
                load_topics, inputs=topics_file_path, outputs=[current_topic, topics]
            )
            current_topic.change(fn=load_video_paths, inputs=[topics_file_path, current_topic], outputs=[current_video_path, video_paths])
            current_video_path.change(fn=lambda path: gr.Video(path, height="80vh"), inputs=current_video_path, outputs=video_player)
            next_video_button.click(next_choice, inputs=[current_video_path, video_paths], outputs=current_video_path)
            next_topic_button.click(next_choice, inputs=[current_topic, topics], outputs=current_topic)
            
        with gr.Tab("Upload to YouTube (Local Machine Only)"):
            def run_upload(topics, publish_date, day_per_video, progress=gr.Progress(track_tqdm=True)):
                YTUploader_string_stream.truncate(0)
                YTUploader_string_stream.seek(0)
                
                uploader = upload_YouTube.YouTubeUploader(logger=YTUploader_logger)
                for _ in uploader.authenticate_youtube():
                    yield YTUploader_string_stream.getvalue()
                for _ in uploader.upload_from_topic_file(topics, publish_date, int(day_per_video)):
                    yield YTUploader_string_stream.getvalue()
                yield YTUploader_string_stream.getvalue()

            with gr.Row():
                publish_date = datetime.datetime.combine(datetime.date.today(), datetime.time(8, 0)).strftime("%d/%m/%Y, %H:%M:%S")
                publish_date = gr.DateTime(value=publish_date, label="Publish Date (YYYY-MM-DD HH:MM)", type='datetime')
                day_per_video = gr.Slider(minimum=1, maximum=14, value=1, step=1, label="Day per video")
                upload_button = gr.Button("Upload Videos", variant="primary")
            upload_progress = gr.Textbox(label="Progress Bar")
            upload_outputs = gr.Textbox(label="Output", lines=30, max_lines=30)
            upload_button.click(
                fn=run_upload,
                inputs=[topics_file_path, publish_date, day_per_video],
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

        make_proposals_and_generate_videos_button.click(
            fn=yt_url_to_proposals.transcribe_and_make_proposals, 
            inputs=[yt_urls_and_series, new_topics_file_path, ollama_model_transcribe], 
            outputs=make_proposals_outputs
        ).success(
            fn=lambda outputs: outputs + "Now go to 'Process Text-to-YTShorts Batch' Tab to see Shorts generation progress.\n",
            inputs=make_proposals_outputs,
            outputs=make_proposals_outputs
        ).success(
            fn=run_text2YTVideos_batch,
            inputs=[new_topics_file_path, send_email_checkbox, make_shorts_checkbox, ollama_model_text2YTVideos, interrupt_flag_path],
            outputs=text2YTVideos_batch_outputs,
            show_progress_on=text2YTVideos_batch_progress,
            show_progress="full",
            scroll_to_output=True
        )

    return demo

if __name__ == "__main__":
    demo = create_demo()
    demo.launch(
        server_name="0.0.0.0",
        server_port=1388,
        # share=True,
        )