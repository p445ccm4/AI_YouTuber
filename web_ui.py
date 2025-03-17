import os
import gradio as gr
import time

# --- Import Functions Directly ---
import ZZZ_print_status
import ZZZ_print_titles
import text2YTShorts_batch
import upload_YouTube

# --- Gradio Interface ---
def create_demo():
    with gr.Blocks() as demo:
        with gr.Column(): # Wrap in a column to ensure topic_file_output is at the top
            topic_file_path = gr.Textbox(label="Enter topic file name: f\"inputs/{topic_file_basename}.topics\"", value="inputs/20250306.topics")
            load_path_btn = gr.Button("Load File")
            topic_file_content = gr.Code(label="Topic File Content", language='shell', interactive=True, max_lines=30)
            save_button = gr.Button("Save Topic File")

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

            load_path_btn.click(load_file_content, inputs=topic_file_path, outputs=topic_file_content)
            save_button.click(save_file_content, inputs=[topic_file_path, topic_file_content], outputs=gr.Text("", label="Last Update"))

        with gr.Tab("text2YTShorts_batch"):
            gr.Interface(
                fn=text2YTShorts_batch.text2YTShorts_batch,
                inputs=[topic_file_path, gr.Checkbox(label="Send Email", value=False)],
                outputs=gr.Textbox(label="Output", max_lines=30),
                title="text2YTShorts_batch",
                flagging_mode="never",
                submit_btn="Generate",
                stop_btn="Stop"
            )
        with gr.Tab("upload_youtube"):
            authenticate_button = gr.Button("Authenticate YouTube")
            uploader = gr.State()
            upload_button = gr.Button("Upload all uncommented videos")

            authenticate_button.click(
                fn=lambda x: upload_YouTube.YouTubeUploader(x),
                inputs=uploader,
                outputs=uploader,
                )
            upload_button.click(
                fn=upload_YouTube.upload_youtube_func,
                inputs=[topic_file_path, uploader],
                outputs=gr.Textbox(label="Output", max_lines=30),
            )
        with gr.Tab("print_status"):
            gr.Interface(
                fn=ZZZ_print_status.print_status,
                inputs=topic_file_path,
                outputs=gr.Code(label="Output", language='shell', interactive=True),
                title="print_status",
                flagging_mode="never",
                submit_btn="Print",
            )
        with gr.Tab("print_titles"):
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
    # demo.launch()