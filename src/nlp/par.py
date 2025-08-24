from nlp.span import Span

class Par(Span):
    def __str__(self):
        p = '\n'
        for o in self.objects:
            p = p + str(o)
        return p
