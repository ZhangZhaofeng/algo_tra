import time

class Hilo:
    def __init__(self):
        print("Hilo initialized")

    def get_hilo_price(self):
        # need work
        return 1000000

    def get_current_price(self):
        # need work
        return 990000

    def get_next_hour(self):
        # need modification
        return time.time() + 3600

    def get_require_colleral_and_type(self):
        # need work
        if 1:
            require_colleral = 0.0
            type = "none"
        elif 1:
            require_colleral = 5000.
            type = "long"
        elif 1:
            require_colleral = 5000.
            type = "short"
        return (require_colleral, type)

    def place_stop_order(self, conditional_price, long_short, type, slide=500):
        # need work
        return True

    def check_position(self):
        # need work
        if 1:
            return "long"
        elif 0:
            return "short"
        else:
            return "none"

    def check_order(self, long_short):
        # need work
        (require_colleral, type) = self.get_require_colleral_and_type()
        if require_colleral > 0.0 and long_short == type:
            return True
        else:
            return False

    def verify_order(self, long_short):
        counter = 0
        while 1:
            if self.check_order(long_short):
                return True
            elif counter > 20:
                return False
            else:
                time.sleep(5)
                counter += 1

    def verify_order_or_position(self, long_short):
        # Wait until the placed order is verified successfully
        if not self.verify_order(long_short):
            if self.check_position() != long_short:
                print("Order verification fails. Trying again")
            else:
                print("Order is filled immediately")
        else:
            print("Order is verified")

    def hilo_run(self):
        while True:
            NEXT_HOUR = self.get_next_hour()
            hilo_price = self.get_hilo_price()  # change once an hour

            while True:  # Do in the current hour
                current_time = time.time()
                if current_time > NEXT_HOUR:
                    break
                current_price = self.get_current_price()

                if self.check_position() == "none":
                    if not self.check_order("short") and not self.check_order("long"):
                        if current_price < hilo_price:
                            self.place_stop_order(hilo_price, "long", "new")
                            self.verify_order_or_position("long")
                        else:
                            self.place_stop_order(hilo_price, "short", "new")
                            self.verify_order_or_position("short")
                    else:
                        print("######current time: %s #####" % current_time)
                        print("Case A: No position. Order is not filled")
                        print("current:%s VS hilo_price:%s" % current_price % hilo_price)
                elif self.check_position() == "long":
                    if not self.check_order("short"):
                        if current_price > hilo_price:  # normal case
                            self.place_stop_order(hilo_price, "short", "change")
                        else:
                            self.place_stop_order(current_price, "short", "change")
                        self.verify_order_or_position("short")
                    else:
                        print("######current time: %s #####" % current_time)
                        print("Case B: Long position. Short order is not filled")
                        print("current:%s VS hilo_price:%s" % current_price % hilo_price)
                elif self.check_position() == "short":
                    if not self.check_order("short"):
                        if current_price < hilo_price:  # normal case
                            self.place_stop_order(hilo_price, "long", "change")
                        else:
                            self.place_stop_order(current_price, "long", "change")
                        self.verify_order_or_position("long")
                    else:
                        print("######current time: %s #####" % current_time)
                        print("Case C: Short position. Long order is not filled")
                        print("current:%s VS hilo_price:%s" % current_price % hilo_price)
                else:
                    print("Abnormal position case")


if __name__ == '__main__':
    my_hilo = Hilo()
    my_hilo.hilo_run()
