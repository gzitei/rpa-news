from abc import ABC, abstractmethod


class Bot(ABC):
    """
    Abstract base class representing a bot.

    This class defines the interface for creating a bot with essential methods
    for configuration, environment setup, exception handling, job lifecycle,
    and runtime behavior.

    Subclasses must implement all abstract methods defined in this class.

    Methods:
        set_config(): Set configuration parameters for the bot.
        set_env(): Set up the environment required by the bot.
        handle_exception(): Handle exceptions that occur during bot execution.
        run(): Start the execution of the bot.
        stop(): Stop the execution of the bot.
        next_job(): Perform the next operation or step in the bot's logic.
        start_job(): Begin a new job or task within the bot's workflow.
        finish_job(): Finish the current job or task within the bot's workflow.
    """

    @abstractmethod
    def set_config(self):
        """
        Set configuration parameters for the bot.

        This method should be implemented by subclasses to set up necessary
        configuration parameters for the bot's operation.
        """
        pass

    @abstractmethod
    def set_env(self):
        """
        Set up the environment required by the bot.

        This method should be implemented by subclasses to prepare the
        necessary environment for the bot's execution.
        """
        pass

    @abstractmethod
    def handle_exception(self):
        """
        Handle exceptions that occur during bot execution.

        Subclasses should implement this method to define how exceptions
        are handled during the bot's execution.
        """
        pass

    @abstractmethod
    def run(self):
        """
        Start the execution of the bot.

        Subclasses should implement this method to define how the bot
        should start its execution
        """
        pass

    @abstractmethod
    def stop(self):
        """
        Stop the execution of the bot.

        Subclasses should implement this method to define how the bot
        should gracefully stop its execution.
        """
        pass

    @abstractmethod
    def next_job(self):
        """
        Perform the next operation or step in the bot's logic.

        Subclasses should implement this method to define the next
        logical step or operation that the bot should perform.
        """
        pass

    @abstractmethod
    def start_job(self):
        """
        Begin a new job or task within the bot's workflow.

        Subclasses should implement this method to define how the bot
        should start a new job or task in its workflow.
        """
        pass

    @abstractmethod
    def finish_job(self):
        """
        Finish the current job or task within the bot's workflow.

        Subclasses should implement this method to define how the bot
        should finish the current job or task in its workflow.
        """
        pass
