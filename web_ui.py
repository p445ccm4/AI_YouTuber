import gradio as gr

# --- Import Functions Directly ---
import ZZZ_print_status
import ZZZ_print_titles
import text2YTShorts_batch
import upload_YouTube

# --- Gradio Interface ---
def create_demo():
    with gr.Blocks() as demo:
        with gr.Column(): # Wrap in a column to ensure topic_file_output is at the top
            topic_file_output = gr.File(file_types=['.topics'], label="Upload Topic File")
            topic_file_content = gr.Code(label="Topic File Content", language='shell', interactive=True)
            save_button = gr.Button("Save Topic File")

            def load_file_content(file_obj):
                if file_obj:
                    file_path = file_obj.name
                    with open(file_path, 'r') as f:
                        content = f.read()
                    return content
                return ""

            def save_file_content(file_obj, content):
                if file_obj:
                    file_path = file_obj.name
                    with open(file_path, 'w') as f:
                        f.write(content)
                    return "File Saved!"
                return "No file uploaded to save."

            topic_file_output.upload(load_file_content, inputs=topic_file_output, outputs=topic_file_content)
            save_button.click(save_file_content, inputs=[topic_file_output, topic_file_content], outputs=gr.Text("Save Status"))

        with gr.Tab("text2YTShorts_batch"):
            gr.Interface(
                fn=lambda topic_file_obj: text2YTShorts_batch.text2YTShorts_batch_func(topic_file_obj.name) if topic_file_obj else "No topic file uploaded.",
                inputs=topic_file_output,
                outputs=gr.Code(label="Output", language='shell'),
                title="text2YTShorts_batch"
            )
        with gr.Tab("upload_youtube"):
            gr.Interface(
                fn=lambda topic_file_obj: upload_YouTube.upload_youtube_func(topic_file_obj.name) if topic_file_obj else "No topic file uploaded.",
                inputs=topic_file_output,
                outputs=gr.Code(label="Output", language='shell'),
                title="upload_youtube"
            )
        with gr.Tab("print_status"):
            gr.Interface(
                fn=lambda topic_file_obj: ZZZ_print_status.print_status(topic_file_obj.name) if topic_file_obj else "No topic file uploaded.",
                inputs=topic_file_output,
                outputs=gr.Code(label="Output", language='shell'),
                title="print_status"
            )
        with gr.Tab("print_titles"):
            gr.Interface(
                fn=lambda folder_path: ZZZ_print_titles.print_titles(folder_path),
                inputs=gr.Textbox("inputs/proposals", label="Folder Path"),
                outputs=gr.Code(label="Output", language='markdown'),
                title="print_titles"
            )

    return demo

if __name__ == "__main__":
    demo = create_demo()
    demo.launch(share=True)