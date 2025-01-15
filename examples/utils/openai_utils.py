from openai import OpenAI


def get_completion(prompt, model="gpt-4o"):
    client = OpenAI(
        api_key="",
    )
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model=model,
    )
    return chat_completion.choices[0].message.content


def generate_unit_tests(file_name):
    file_path = f"../src/{file_name}.py"
    with open(file_path, "r") as file:
        source_code = file.read()

    with open('../tests/test_00_consumer.py', "r") as file:
        example_test_code = file.read()

    prompt = f"""
        Please generate unit tests for source code.
        Just keep valid Python code, don't include Explanation or other non-code part in the response, and don't include
        python code annotation before and after the code lines, ike '```python' and '```'.

        The unit tests is using pact to do contract tests. The libraries used and the format for the test files, you can
        take '''{example_test_code}''' as a reference.
        Take note:
        1. The test code's style should follow PEP 8.
        2. When importing source code below src folder, you should append 'examples.' before 'src'
        3. When importing source classes, you need to from the '''{file_name}''' to import, for example,
        if the file name is company_consumer, you need to import by like 'from examples.src.company_consumer import Company, CompanyConsumer'

        Source code: '''{source_code}'''
        """
    res = get_completion(prompt)
    with open(f"../tests/test_generated_{file_name}.py", 'w') as f:
        f.write(res)

    print(f"Test case for source file {file_name} generated.")


if __name__ == "__main__":
    file_name = 'employee_consumer'
    generate_unit_tests(file_name)
