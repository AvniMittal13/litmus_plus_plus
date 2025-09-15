from agents.main_agent import MainAgent

def main():
    # Initialize the main agent
    main_agent = MainAgent()
    
    print("Welcome to Litmus Agent! Type 'exit' or 'quit' to stop.")
    print("-" * 50)
    
    while True:
        try:
            # Get user input
            user_input = input("\nEnter your query: ").strip()
            
            # Check for exit conditions
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("Goodbye!")
                break
            
            # Skip empty inputs
            if not user_input:
                print("Please enter a valid query.")
                continue
            
            # Process the query through main agent
            print("\nProcessing your query...")
            response = main_agent.run(user_input)
            
            # Display the response
            print("\nResponse:")
            print("-" * 30)
            print(response)
            print("-" * 30)
            
        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Goodbye!")
            break
        except Exception as e:
            print(f"\nError occurred: {e}")
            print("Please try again.")

if __name__ == "__main__":
    main()